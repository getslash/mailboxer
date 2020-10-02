use crate::schema::mailbox;
use crate::utils::{ConnectionPool, LoggedResult};
use actix::prelude::*;
use diesel::prelude::*;
use failure::Error;
use log::debug;
use std::time::{Duration, SystemTime};

const VACUUM_CUTOFF_SECS: u64 = 24 * 60 * 60 * 7; // one week
const VACUUM_INTERVAL_SECS: u64 = 60 * 60;

pub struct VacuumCleaner {
    connection_pool: ConnectionPool,
}

impl VacuumCleaner {
    pub fn new(connection_pool: ConnectionPool) -> VacuumCleaner {
        VacuumCleaner { connection_pool }
    }
}

struct Vacuum;

impl Message for Vacuum {
    type Result = Result<(), Error>;
}

impl Actor for VacuumCleaner {
    type Context = Context<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        ctx.run_interval(Duration::new(VACUUM_INTERVAL_SECS, 0), |_actor, ctx| {
            ctx.notify(Vacuum)
        });
    }
}

impl Handler<Vacuum> for VacuumCleaner {
    type Result = Result<(), Error>;

    fn handle(&mut self, _msg: Vacuum, _ctx: &mut Context<Self>) -> Self::Result {
        vacuum_old_mailboxes(&self.connection_pool).log_errors()
    }
}

pub fn vacuum_old_mailboxes(pool: &ConnectionPool) -> Result<(), Error> {
    let cutoff = SystemTime::now() - Duration::from_secs(VACUUM_CUTOFF_SECS);
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
