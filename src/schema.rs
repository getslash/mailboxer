table! {
    email (id) {
        id -> Int4,
        mailbox_id -> Int4,
        fromaddr -> Varchar,
        message -> Text,
        timestamp -> Timestamp,
        sent_via_ssl -> Bool,
        read -> Bool,
    }
}

table! {
    mailbox (id) {
        id -> Int4,
        address -> Varchar,
        last_activity -> Timestamp,
    }
}

joinable!(email -> mailbox (mailbox_id));

allow_tables_to_appear_in_same_query!(
    email,
    mailbox,
);
