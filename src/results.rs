use actix_web::{Error, HttpRequest, HttpResponse, Responder, Result};
use pagination::Pagination;
use serde::Serialize;

pub struct Success;

pub enum APIResult<T: Serialize> {
    QueryResult(Vec<T>, Pagination),
    SingleResult(T),
}

impl<T: Serialize> APIResult<T> {
    pub fn multiple(result: Vec<T>, pagination: Pagination) -> Self {
        APIResult::QueryResult(result, pagination)
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
            APIResult::QueryResult(results, pagination) => json!({
                "result": results,
                "metadata": {
                    "page": pagination.get_page(),
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
