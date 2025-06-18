-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- Create enum for post status
create type post_status as enum ('active', 'deleted', 'archived');

-- Create profiles table
create table if not exists profiles (
    id uuid primary key default uuid_generate_v4(),
    username text not null unique,
    display_name text,
    bio text,
    profile_image_url text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create posts table
create table if not exists posts (
    id uuid primary key default uuid_generate_v4(),
    profile_id uuid references profiles(id) on delete cascade,
    content text not null,
    posted_at timestamp with time zone not null,
    likes_count integer not null default 0,
    comments_count integer not null default 0,
    status post_status default 'active',
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create media table
create table if not exists media (
    id uuid primary key default uuid_generate_v4(),
    post_id uuid references posts(id) on delete cascade,
    url text not null,
    local_path text,
    media_type text not null,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create indexes if they don't exist
do $$ 
begin
    if not exists (select 1 from pg_indexes where indexname = 'posts_profile_id_idx') then
        create index posts_profile_id_idx on posts(profile_id);
    end if;
    if not exists (select 1 from pg_indexes where indexname = 'posts_posted_at_idx') then
        create index posts_posted_at_idx on posts(posted_at);
    end if;
    if not exists (select 1 from pg_indexes where indexname = 'posts_status_idx') then
        create index posts_status_idx on posts(status);
    end if;
    if not exists (select 1 from pg_indexes where indexname = 'media_post_id_idx') then
        create index media_post_id_idx on media(post_id);
    end if;
end $$;

-- Create updated_at trigger function if it doesn't exist
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = timezone('utc'::text, now());
    return new;
end;
$$ language plpgsql;

-- Create triggers if they don't exist
do $$ 
begin
    if not exists (select 1 from pg_trigger where tgname = 'update_posts_updated_at') then
        create trigger update_posts_updated_at
            before update on posts
            for each row
            execute function update_updated_at_column();
    end if;
    if not exists (select 1 from pg_trigger where tgname = 'update_profiles_updated_at') then
        create trigger update_profiles_updated_at
            before update on profiles
            for each row
            execute function update_updated_at_column();
    end if;
end $$;
