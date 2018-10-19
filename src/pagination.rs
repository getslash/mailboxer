use std::cmp::max;

#[derive(Deserialize, Debug)]
pub struct Pagination {
    page: Option<u64>,
    page_size: Option<u64>,
}

impl Pagination {
    pub fn get_page(&self) -> i64 {
        max(1, self.page.unwrap_or(1) as i64)
    }

    pub fn get_page_size(&self) -> i64 {
        max(1, self.page_size.unwrap_or(500) as i64)
    }

    pub fn get_offset(&self) -> i64 {
        (self.get_page() - 1) * self.get_page_size()
    }
}
