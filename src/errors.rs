use actix_web::{error, http, HttpResponse};
use std::convert::From;

#[derive(thiserror::Error, Debug)]
pub enum MailboxerError {
    #[error("Mailbox already exists")]
    MailboxAlreadyExists,
    #[error("Mailbox not found")]
    MailboxNotFound,
    #[error("Internal error")]
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
            ref e @ MailboxerError::MailboxNotFound => HttpResponse::NotFound().body(e.to_string()),
        }
    }
}
