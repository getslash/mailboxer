use serde_derive::Serialize;
use std::time::SystemTime;

#[derive(Queryable, Serialize)]
pub struct Mailbox {
    pub id: i32,
    pub address: String,
    pub last_activity: SystemTime,
}

#[derive(Queryable, Serialize)]
pub struct Email {
    pub id: i32,
    pub mailbox_id: i32,
    pub fromaddr: String,
    pub message: String,
    pub timestamp: SystemTime,
    pub sent_via_ssl: bool,
    pub read: bool,
}
