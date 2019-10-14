use crate::errors::MailboxerError;
use crate::models::{Email, Mailbox};
use crate::pagination::Pagination;
use crate::results::*;
use crate::schema::{email, mailbox};
use crate::utils::{ConnectionPool, LoggedResult};
use crate::vacuum::vacuum_old_mailboxes;
use actix_web::{Json, Path, Query, Result, State};
use diesel;
use diesel::{
    prelude::*,
    result::{DatabaseErrorKind::UniqueViolation, Error::DatabaseError},
    QueryDsl,
};
use failure::Error;
use serde_derive::Deserialize;
use std::time::{Duration, SystemTime};

const _PAGE_SIZE: usize = 1000;

#[derive(Deserialize)]
pub struct NewMailbox {
    address: String,
}

pub fn make_inactive(
    (mailbox_address, pool): (Path<String>, State<ConnectionPool>),
) -> Result<Success, MailboxerError> {
    let conn = pool.get()?;
    if let Some(mb) = mailbox::table
        .filter(mailbox::columns::address.eq(mailbox_address.as_ref()))
        .first::<Mailbox>(&conn)
        .optional()?
    {
        diesel::update(mailbox::table.filter(mailbox::columns::id.eq(mb.id)))
            .set(
                mailbox::columns::last_activity
                    .eq(SystemTime::now() - Duration::from_secs(500 * 24 * 60 * 60)),
            )
            .execute(&conn)
            .log_errors()?;
        Ok(Success)
    } else {
        Err(MailboxerError::MailboxNotFound)
    }
}

#[cfg_attr(feature = "cargo-clippy", allow(clippy::needless_pass_by_value))]
pub fn vacuum(pool: State<ConnectionPool>) -> Result<Success, MailboxerError> {
    vacuum_old_mailboxes(&pool)
        .map_err(|_| MailboxerError::InternalServerError)
        .log_errors()?;
    Ok(Success)
}

pub fn query_mailboxes(
    (connmgr, pagination): (State<ConnectionPool>, Query<Pagination>),
) -> Result<APIResult<Mailbox>, Error> {
    let query = mailbox::table
        .order_by(mailbox::columns::last_activity.desc())
        .offset(pagination.get_offset())
        .limit(pagination.get_page_size());
    Ok(APIResult::multiple(
        query.load::<Mailbox>(&connmgr.get()?)?,
        pagination.into_inner(),
    ))
}

pub fn query_single_mailbox(
    (mailbox_address, pool): (Path<String>, State<ConnectionPool>),
) -> Result<APIResult<Mailbox>, MailboxerError> {
    let conn = pool.get()?;
    if let Some(mb) = mailbox::table
        .filter(mailbox::columns::address.eq(mailbox_address.as_ref()))
        .first::<Mailbox>(&conn)
        .optional()?
    {
        Ok(APIResult::single(mb))
    } else {
        Err(MailboxerError::MailboxNotFound)
    }
}

pub fn create_mailbox(
    (new_mailbox, state): (Json<NewMailbox>, State<ConnectionPool>),
) -> Result<Success, MailboxerError> {
    let address = new_mailbox.into_inner().address;

    let conn = state.get().log_errors()?;

    let res = diesel::insert_into(mailbox::table)
        .values(mailbox::dsl::address.eq(&address))
        .execute(&conn)
        .log_errors();
    if let Err(DatabaseError(UniqueViolation, _)) = res {
        return Err(MailboxerError::MailboxAlreadyExists);
    }
    res.log_errors()?;
    Ok(Success)
}

pub fn delete_mailbox(
    (mailbox_address, pool): (Path<String>, State<ConnectionPool>),
) -> Result<Success, MailboxerError> {
    diesel::delete(mailbox::table.filter(mailbox::columns::address.eq(mailbox_address.as_ref())))
        .execute(&pool.get()?)
        .map(|_| Success)
        .log_errors()
        .map_err(MailboxerError::from)
}

pub fn query_unread_emails(
    (address, pool, pagination): (Path<String>, State<ConnectionPool>, Query<Pagination>),
) -> Result<APIResult<Email>, MailboxerError> {
    query_emails(address.as_ref(), &pool, pagination.into_inner(), false)
}

pub fn query_all_emails(
    (address, pool, pagination): (Path<String>, State<ConnectionPool>, Query<Pagination>),
) -> Result<APIResult<Email>, MailboxerError> {
    query_emails(address.as_ref(), &pool, pagination.into_inner(), true)
}

pub fn query_emails(
    address: &str,
    pool: &ConnectionPool,
    pagination: Pagination,
    include_read: bool,
) -> Result<APIResult<Email>, MailboxerError> {
    let conn = pool.get()?;
    if let Some(mailbox) = mailbox::table
        .filter(mailbox::columns::address.eq(address))
        .first::<Mailbox>(&conn)
        .optional()?
    {
        let mut query = email::table.into_boxed();

        query = query.filter(email::columns::mailbox_id.eq(mailbox.id));
        if !include_read {
            query = query.filter(email::columns::read.eq(false));
        }
        query = query.order_by(email::columns::timestamp);
        query = query
            .offset(pagination.get_offset())
            .limit(pagination.get_page_size());

        let emails = query.load::<Email>(&conn)?;
        let unread_ids: Vec<_> = emails.iter().filter(|e| !e.read).map(|e| e.id).collect();

        if !unread_ids.is_empty() {
            diesel::update(email::table.filter(email::columns::id.eq_any(&unread_ids)))
                .set(email::columns::read.eq(true))
                .execute(&conn)?;
        }

        Ok(APIResult::multiple(emails, pagination))
    } else {
        Err(MailboxerError::MailboxNotFound)
    }
}
