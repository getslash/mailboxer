use serde::Deserialize;
use std::cmp::max;

#[derive(Deserialize, Debug)]
pub struct Pagination {
    page: Option<usize>,
    page_size: Option<usize>,
}

impl Pagination {
    pub fn get_page(&self) -> usize {
        max(1, self.page.unwrap_or(1) as usize)
    }

    pub fn limit(&self) -> i64 {
        self.get_page_size() as i64
    }

    pub fn get_page_size(&self) -> usize {
        max(1, self.page_size.unwrap_or(500))
    }

    pub fn offset(&self) -> i64 {
        ((self.get_page() - 1) * self.get_page_size()) as i64
    }
}
