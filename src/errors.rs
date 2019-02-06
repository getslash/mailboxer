use actix_web::{error, http, HttpResponse};
use diesel;
use failure::Fail;
use r2d2;
use std::convert::From;

#[derive(Fail, Debug)]
pub enum MailboxerError {
    #[fail(display = "Mailbox already exists")]
    MailboxAlreadyExists,
    #[fail(display = "Mailbox not found")]
    MailboxNotFound,
    #[fail(display = "Internal error")]
    InternalServerError,
}

impl From<diesel::result::Error> for MailboxerError {
    fn from(_err: diesel::result::Error) -> Self {
        MailboxerError::InternalServerError
    }
}

impl From<r2d2::Error> for MailboxerError {
    fn from(_err: r2d2::Error) -> Self {
        MailboxerError::InternalServerError
    }
}

impl error::ResponseError for MailboxerError {
    fn error_response(&self) -> HttpResponse {
        match *self {
            MailboxerError::MailboxAlreadyExists => HttpResponse::new(http::StatusCode::CONFLICT),
            MailboxerError::InternalServerError => {
                HttpResponse::new(http::StatusCode::INTERNAL_SERVER_ERROR)
            }
            ref e @ MailboxerError::MailboxNotFound => {
                HttpResponse::with_body(http::StatusCode::NOT_FOUND, e.to_string())
            }
        }
    }
}
