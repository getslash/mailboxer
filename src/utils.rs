use diesel::pg::PgConnection;
use diesel::r2d2::ConnectionManager;
use failure::AsFail;
use r2d2;
use sentry::integrations::failure::capture_fail;
use std::fmt::Debug;

pub trait StartsWithIgnoreCase {
    fn starts_with_ignore_case(&self, prefix: &str) -> bool;
}

impl StartsWithIgnoreCase for str {
    fn starts_with_ignore_case(&self, prefix: &str) -> bool {
        if prefix.len() > self.len() {
            return false;
        }
        self[..prefix.len()].eq_ignore_ascii_case(prefix)
    }
}

pub type ConnectionPool = r2d2::Pool<ConnectionManager<PgConnection>>;

mod test {

    #[cfg(test)]
    use super::StartsWithIgnoreCase;

    #[test]
    fn test_starts_with_ignore_case() {
        assert!("hello".starts_with_ignore_case("HE"));
        assert!("hello".starts_with_ignore_case("He"));
        assert!("hello".starts_with_ignore_case("HEll"));
        assert!("hello".starts_with_ignore_case("hello"));
        assert!(!"hello".starts_with_ignore_case("hello1"));
    }
}

pub trait LoggedResult {
    fn log_errors(self) -> Self;
}

impl<T, E: AsFail + Debug> LoggedResult for Result<T, E> {
    fn log_errors(self) -> Self {
        self.map_err(|e| {
            error!("Error encountered: {:?}", e);
            let _ = capture_fail(e.as_fail());
            e
        })
    }
}
