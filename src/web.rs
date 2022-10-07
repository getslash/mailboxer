use crate::api;
use actix_web::web;

pub fn configure_routes(config: &mut web::ServiceConfig) {
    config
        .route(
            "/v2/_debug/make_inactive/{address}",
            web::post().to(api::make_inactive),
        )
        .service(
            web::resource("/v2/mailboxes")
                .route(web::get().to(api::query_mailboxes))
                .route(web::post().to(api::create_mailbox)),
        )
        .service(
            web::resource("/v2/mailboxes/{address}")
                .route(web::get().to(api::query_single_mailbox))
                .route(web::delete().to(api::delete_mailbox)),
        )
        .service(
            web::resource("/v2/mailboxes/{address}/emails")
                .route(web::get().to(api::query_all_emails)),
        )
        .route(
            "/v2/mailboxes/{address}/unread_emails",
            web::get().to(api::query_unread_emails),
        )
        .route("/v2/vacuum", web::post().to(api::vacuum));
}
