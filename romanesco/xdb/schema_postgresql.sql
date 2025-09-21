create table if not exists receipts (
    id            integer primary key generated always as identity,
    timestamp     integer not null,
    comment       text not null,
    cached_totals text,
    automatic     boolean not null default false
);
create index if not exists ix_receipts_timestamp on receipts(timestamp);

create table if not exists categories (
    id      integer primary key generated always as identity,
    name    text not null
);

create table if not exists items (
    id          integer primary key generated always as identity,
    name        text not null,
    ean         text,
    splits      text,
    category_id integer not null,
    last_use    integer,
    foreign key(category_id) references categories(id)
);
create index if not exists ix_items_ean on items(ean) where ean is not null;

create table if not exists receipts_items (
    item_id     integer not null,
    receipt_id  integer not null,
    quantity    numeric not null,
    price       numeric not null,
    sort        integer not null,
    primary key(item_id, receipt_id),
    foreign key(item_id) references items(id),
    foreign key(receipt_id) references receipts(id) on delete cascade
);
create index if not exists ix_receipts_items_receipt_id on receipts_items(receipt_id);

create table if not exists users (
    id      integer primary key generated always as identity,
    name    text unique not null,
    net     numeric not null,
    email   text,
    target  numeric
);

create table if not exists deposits (
    user_id    integer not null,
    timestamp  integer not null,
    amount     numeric not null,
    comment    text,
    foreign key(user_id) references users(id)
);
create index if not exists ix_deposits_timestamp on deposits(timestamp);

create table if not exists stats_total (
    user_id     integer not null,
    category_id integer,
    year        integer not null,
    month       integer not null,
    total       numeric not null,
    unique nulls not distinct(user_id, year, month, category_id),
    foreign key(user_id) references users(id),
    foreign key(category_id) references categories(id)
);
create table if not exists stats_days (
    user_id     integer not null,
    category_id integer,
    day         integer not null,
    total       numeric not null,
    unique nulls not distinct(user_id, category_id, day),
    foreign key(user_id) references users(id),
    foreign key(category_id) references categories(id)
);

create table if not exists botccoli_config (
    config_id    integer primary key generated always as identity,
    user_id      integer not null,
    adapter_key  text not null,
    last_id      text,
    last_date    integer,
    user_enc     text not null,
    passwd_enc   text not null,
    cookies_json text,
    foreign key(user_id) references users(id)
);
