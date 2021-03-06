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
use crate::vacuum::VacuumCleaner;
use crate::web::make_app;
use actix::prelude::*;
use actix_web::server;
use diesel::r2d2::ConnectionManager;
use dotenv::dotenv;
use env_logger::Builder;
use failure::Error;
use log::{debug, error};
use std::env;
use std::net::TcpListener;

fn main() {
    dotenv().ok();

    let _guard = sentry::init(env::var("SENTRY_DSN").ok());
    env::set_var("RUST_BACKTRACE", "1");
    sentry::integrations::panic::register_panic_handler();

    Builder::new()
        .filter_module("mailboxer", log::LevelFilter::Debug)
        .filter_module("actix_web", log::LevelFilter::Debug)
        .init();

    debug!("Mailboxer starting...");

    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let connmgr = r2d2::Pool::builder()
        .max_size(16)
        .build(ConnectionManager::new(database_url))
        .expect("Unable to initialize pool manager");

    debug!("Running migrations...");

    run_migrations(&connmgr).expect("Unable to run migrations");

    debug!("Migrations complete. Starting system...");

    let sys = System::new("mailboxer");

    let _vacuum = VacuumCleaner::new(connmgr.clone()).start();

    let bind_addr = "0.0.0.0:2525";
    let listener = TcpListener::bind(bind_addr).unwrap();
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

    server::new(move || make_app(connmgr.clone()))
        .bind("0.0.0.0:8000")
        .expect("Cannot bind port")
        .system_exit()
        .start();
    sys.run();
}

fn run_migrations(connmgr: &ConnectionPool) -> Result<(), Error> {
    embed_migrations!();
    let conn = connmgr.get()?;

    embedded_migrations::run(&conn)
        .map_err(Error::from)
        .map(drop)
}
