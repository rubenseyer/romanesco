create table if not exists receipts (
    id            integer primary key not null,
    timestamp     integer not null,
    comment       text not null,
    cached_totals text
);
create index if not exists ix_receipts_timestamp on receipts(timestamp);

create table if not exists items (
    id          integer primary key not null,
    name        text not null,
    ean         text,
    splits      text,
    category_id integer not null,
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
    primary key(user_id, category_id, year, month),
    foreign key(user_id) references users(id),
    foreign key(category_id) references categories(id)
);
create table if not exists stats_avg (
    user_id     integer not null,
    category_id integer,
    day         integer not null,
    cum_avg     text not null,
    avg         text not null,
    nobs        integer default null,
    primary key(user_id, category_id, day),
    foreign key(user_id) references users(id),
    foreign key(category_id) references categories(id)
);
