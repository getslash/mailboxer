use crate::errors::MailboxerError;
use crate::models::{Email, Mailbox};
use crate::pagination::Pagination;
use crate::results::*;
use crate::schema::{email, mailbox};
use crate::utils::{ConnectionPool, LoggedResult};
use crate::vacuum::vacuum_old_mailboxes;
use actix_web::{
    web::{Data, Json, Path, Query},
    Result,
};
use diesel::{
    prelude::*,
    result::{DatabaseErrorKind::UniqueViolation, Error::DatabaseError},
    QueryDsl,
};
use serde::Deserialize;
use std::time::{Duration, SystemTime};

const _PAGE_SIZE: usize = 1000;

#[derive(Deserialize)]
pub struct NewMailbox {
    address: String,
}

pub async fn make_inactive(
    mailbox_address: Path<String>,
    pool: Data<ConnectionPool>,
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

pub async fn vacuum(pool: Data<ConnectionPool>) -> Result<Success, MailboxerError> {
    vacuum_old_mailboxes(&pool)
        .map_err(|_| MailboxerError::InternalServerError)
        .log_errors()?;
    Ok(Success)
}

pub async fn query_mailboxes(
    connmgr: Data<ConnectionPool>,
    pagination: Query<Pagination>,
) -> Result<APIResult<Mailbox>, MailboxerError> {
    let page_size: usize = pagination.get_page_size();
    let query = mailbox::table
        .order_by(mailbox::columns::last_activity.desc())
        .offset(pagination.offset())
        .limit(pagination.limit() + 1);
    let objs = query.load(&connmgr.get()?)?;
    let has_more = objs.len() > page_size;
    Ok(APIResult::multiple(
        objs.into_iter().take(page_size).collect(),
        pagination.into_inner(),
        has_more,
    ))
}

pub async fn query_single_mailbox(
    (mailbox_address, pool): (Path<String>, Data<ConnectionPool>),
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

pub async fn create_mailbox(
    (new_mailbox, state): (Json<NewMailbox>, Data<ConnectionPool>),
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

pub async fn delete_mailbox(
    (mailbox_address, pool): (Path<String>, Data<ConnectionPool>),
) -> Result<Success, MailboxerError> {
    diesel::delete(mailbox::table.filter(mailbox::columns::address.eq(mailbox_address.as_ref())))
        .execute(&pool.get()?)
        .map(|_| Success)
        .log_errors()
        .map_err(MailboxerError::from)
}

pub async fn query_unread_emails(
    (address, pool, pagination): (Path<String>, Data<ConnectionPool>, Query<Pagination>),
) -> Result<APIResult<Email>, MailboxerError> {
    query_emails(address.as_ref(), &pool, pagination.into_inner(), false).await
}

pub async fn query_all_emails(
    (address, pool, pagination): (Path<String>, Data<ConnectionPool>, Query<Pagination>),
) -> Result<APIResult<Email>, MailboxerError> {
    query_emails(address.as_ref(), &pool, pagination.into_inner(), true).await
}

pub async fn query_emails(
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
            .offset(pagination.offset())
            .limit(pagination.limit() + 1);

        let page_size = pagination.get_page_size();

        let emails = query.load::<Email>(&conn)?;
        let has_more = emails.len() > page_size;
        let unread_ids: Vec<_> = emails.iter().filter(|e| !e.read).map(|e| e.id).collect();

        if !unread_ids.is_empty() {
            diesel::update(email::table.filter(email::columns::id.eq_any(&unread_ids)))
                .set(email::columns::read.eq(true))
                .execute(&conn)?;
        }

        Ok(APIResult::multiple(
            emails.into_iter().take(page_size).collect(),
            pagination,
            has_more,
        ))
    } else {
        Err(MailboxerError::MailboxNotFound)
    }
}
