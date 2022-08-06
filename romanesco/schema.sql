create table if not exists receipts (
    id            integer primary key not null,
    timestamp     integer not null,
    comment       text not null,
    cached_totals text,
    automatic     boolean not null default false
);
create index if not exists ix_receipts_timestamp on receipts(timestamp);

create table if not exists items (
    id          integer primary key not null,
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
    quantity    text not null,
    price       text not null,
    sort        integer not null,
    primary key(item_id, receipt_id),
    foreign key(item_id) references items(id),
    foreign key(receipt_id) references receipts(id)
);
create index if not exists ix_receipts_items_receipt_id on receipts_items(receipt_id);

create table if not exists categories (
    id      integer primary key not null,
    name    text not null
);

create table if not exists users (
    id      integer primary key not null,
    name    text unique not null,
    net     text not null
);

create table if not exists deposits (
    user_id    integer not null,
    timestamp  integer not null,
    amount     text not null,
    comment    text,
    foreign key(user_id) references users(id)
);
create index if not exists ix_deposits_timestamp on deposits(timestamp);

create table if not exists stats_total (
    user_id     integer not null,
    category_id integer,
    year        integer not null,
    month       integer not null,
    total       text not null,
    primary key(user_id, year desc, month desc, category_id),
    foreign key(user_id) references users(id),
    foreign key(category_id) references categories(id)
);
create table if not exists stats_days (
    user_id     integer not null,
    category_id integer,
    day         integer not null,
    total       text not null,
    primary key(user_id, category_id, day),
    foreign key(user_id) references users(id),
    foreign key(category_id) references categories(id)
);

create table if not exists botccoli_config (
    user_id      integer not null,
    adapter_key  text not null,
    last_id      text,
    last_date    integer,
    user_enc     blob not null,
    passwd_enc   blob not null,
    cookies_json blob,
    foreign key(user_id) references users(id)
);
