use actix_web::App;
use api;
use sentry_actix::SentryMiddleware;
use utils::ConnectionPool;

pub fn make_app(pool: ConnectionPool) -> App<ConnectionPool> {
    App::with_state(pool)
        .middleware(SentryMiddleware::new())
        .prefix("/v2")
        .resource("/_debug/make_inactive/{address}", |r| {
            r.post().with(api::make_inactive)
        }).resource("/mailboxes", |r| {
            r.get().with(api::query_mailboxes);
            r.post().with(api::create_mailbox);
        }).resource("/mailboxes/{address}", |r| {
            r.get().with(api::query_single_mailbox);
            r.delete().with(api::delete_mailbox);
        }).resource("/mailboxes/{address}/emails", |r| {
            r.get().with(api::query_all_emails)
        }).resource("/mailboxes/{address}/unread_emails", |r| {
            r.get().with(api::query_unread_emails)
        }).resource("/vacuum", |r| {
            r.post().with(api::vacuum);
        })
}
