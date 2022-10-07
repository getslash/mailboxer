use crate::schema::mailbox;
use crate::utils::{ConnectionPool, LoggedResult};
use diesel::prelude::*;
use log::debug;
use std::time::{Duration, SystemTime};

const VACUUM_CUTOFF: Duration = Duration::from_secs(24 * 60 * 60 * 7); // one week
const VACUUM_INTERVAL: Duration = Duration::from_secs(60 * 60);

pub fn spawn_vacuum(pool: ConnectionPool) {
    std::thread::spawn(move || loop {
        std::thread::sleep(VACUUM_INTERVAL);

        let _ = vacuum_old_mailboxes(&pool).map_err(|e| {
            log::error!("{e:?}");
            sentry::integrations::anyhow::capture_anyhow(&e);
        });
    });
}

pub fn vacuum_old_mailboxes(pool: &ConnectionPool) -> anyhow::Result<()> {
    let cutoff = SystemTime::now() - VACUUM_CUTOFF;
    debug!(
        "Vacuuming - deleting inactive mailboxes older than {:?}...",
        cutoff
    );
    diesel::delete(mailbox::table.filter(mailbox::columns::last_activity.lt(cutoff)))
        .execute(&pool.get()?)
        .log_errors()?;
    debug!("Vacuum complete");
    Ok(())
}
