use crate::pagination::Pagination;
use actix_web::{body::BoxBody, HttpRequest, HttpResponse, Responder};
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
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
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
        HttpResponse::Ok().json(returned)
    }
}

impl Responder for Success {
    type Body = BoxBody;

    fn respond_to(self, _req: &HttpRequest) -> HttpResponse<Self::Body> {
        HttpResponse::Ok().json(json!({"result": "ok"}))
    }
}
