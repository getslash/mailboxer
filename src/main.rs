#![deny(warnings)]

#[macro_use]
extern crate diesel;
#[macro_use]
extern crate diesel_migrations;

mod api;
mod errors;
mod models;
mod pagination;
mod results;
mod schema;
mod smtp;
mod utils;
mod vacuum;
mod web;

use crate::smtp::SMTPSession;
use crate::utils::ConnectionPool;
use crate::vacuum::spawn_vacuum;
use crate::web::configure_routes;
use actix_web::web::Data;
use actix_web::{App, HttpServer};
use anyhow::Context;
use diesel::r2d2::ConnectionManager;
use dotenv::dotenv;
use env_logger::Builder;
use log::{debug, error};
use sentry_actix::Sentry;
use std::env;
use std::net::TcpListener;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenv().ok();

    let _guard = sentry::init(env::var("SENTRY_DSN").ok());
    env::set_var("RUST_BACKTRACE", "1");

    Builder::new()
        .filter_module("mailboxer", log::LevelFilter::Debug)
        .filter_module("actix_web", log::LevelFilter::Debug)
        .init();

    debug!("Mailboxer starting...");

    let database_url = env::var("DATABASE_URL").context("DATABASE_URL must be set")?;
    let connmgr = r2d2::Pool::builder()
        .max_size(16)
        .build(ConnectionManager::new(database_url))
        .context("Unable to initialize pool manager")?;

    debug!("Running migrations...");

    run_migrations(&connmgr).context("Unable to run migrations")?;

    debug!("Migrations complete. Starting system...");

    spawn_vacuum(connmgr.clone());

    let bind_addr = "0.0.0.0:2525";
    let listener = TcpListener::bind(bind_addr)?;
    debug!("SMTP Server listening on {}", bind_addr);

    let smtp_connmgr = connmgr.clone();
    std::thread::spawn(move || {
        for stream in listener.incoming() {
            debug!("Got new connection: {:?}", stream);
            let connmgr = smtp_connmgr.clone();
            std::thread::spawn(move || {
                let res = SMTPSession::new(stream.unwrap()).run(&connmgr);
                if res.is_err() {
                    error!("Error processing request: {:?}", res);
                }
            });
        }
    });

    HttpServer::new(move || {
        App::new()
            .app_data(Data::new(connmgr.clone()))
            .wrap(Sentry::new())
            .configure(configure_routes)
    })
    .bind(("0.0.0.0", 8080))?
    .run()
    .await?;

    Ok(())
}

fn run_migrations(connmgr: &ConnectionPool) -> anyhow::Result<()> {
    embed_migrations!();
    let conn = connmgr.get()?;

    embedded_migrations::run(&conn)
        .map_err(anyhow::Error::from)
        .map(drop)
}
