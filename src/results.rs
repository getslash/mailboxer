use crate::pagination::Pagination;
use actix_web::{Error, HttpRequest, HttpResponse, Responder, Result};
use serde::Serialize;
use serde_json::json;

pub struct Success;

pub enum APIResult<T: Serialize> {
    QueryResult(Vec<T>, Pagination, bool),
    SingleResult(T),
}

impl<T: Serialize> APIResult<T> {
    pub fn multiple(result: Vec<T>, pagination: Pagination, has_more: bool) -> Self {
        APIResult::QueryResult(result, pagination, has_more)
    }

    pub fn single(result: T) -> Self {
        APIResult::SingleResult(result)
    }
}

impl<T: Serialize> Responder for APIResult<T> {
    type Item = HttpResponse;
    type Error = Error;

    fn respond_to<S: 'static>(self, _req: &HttpRequest<S>) -> Result<Self::Item, Self::Error> {
        let returned = match self {
            APIResult::QueryResult(results, pagination, has_more) => json!({
                "result": results,
                "metadata": {
                    "page": pagination.get_page(),
                    "page_size": pagination.get_page_size(),
                    "has_more": has_more,
                }
            }),
            APIResult::SingleResult(result) => json!({
                "result": result,
            }),
        };
        Ok(HttpResponse::Ok().json(returned))
    }
}

impl Responder for Success {
    type Item = HttpResponse;
    type Error = Error;

    fn respond_to<S: 'static>(self, _req: &HttpRequest<S>) -> Result<Self::Item, Self::Error> {
        Ok(HttpResponse::Ok().json(json!({"result": "ok"})))
    }
}
