drop trigger if exists "update_profiles_updated_at" on "public"."profiles";

revoke delete on table "public"."media" from "anon";

revoke insert on table "public"."media" from "anon";

revoke references on table "public"."media" from "anon";

revoke select on table "public"."media" from "anon";

revoke trigger on table "public"."media" from "anon";

revoke truncate on table "public"."media" from "anon";

revoke update on table "public"."media" from "anon";

revoke delete on table "public"."media" from "authenticated";

revoke insert on table "public"."media" from "authenticated";

revoke references on table "public"."media" from "authenticated";

revoke select on table "public"."media" from "authenticated";

revoke trigger on table "public"."media" from "authenticated";

revoke truncate on table "public"."media" from "authenticated";

revoke update on table "public"."media" from "authenticated";

revoke delete on table "public"."media" from "service_role";

revoke insert on table "public"."media" from "service_role";

revoke references on table "public"."media" from "service_role";

revoke select on table "public"."media" from "service_role";

revoke trigger on table "public"."media" from "service_role";

revoke truncate on table "public"."media" from "service_role";

revoke update on table "public"."media" from "service_role";

alter table "public"."media" drop constraint "media_post_id_fkey";

alter table "public"."posts" drop constraint "posts_profile_id_fkey";

alter table "public"."profiles" drop constraint "profiles_username_key";

alter table "public"."media" drop constraint "media_pkey";

drop index if exists "public"."media_pkey";

drop index if exists "public"."media_post_id_idx";

drop index if exists "public"."posts_profile_id_idx";

drop index if exists "public"."posts_status_idx";

drop index if exists "public"."profiles_username_key";

drop index if exists "public"."posts_posted_at_idx";

drop table "public"."media";

create table "public"."user_settings" (
    "id" uuid not null,
    "exchange_credentials" jsonb default '[]'::jsonb,
    "trading_settings" jsonb default '{"maxTradeAmount": 1000, "automationEnabled": false, "monitoredAccounts": [], "maxDailyTradeAmount": 5000, "allowedCryptocurrencies": ["BTC", "ETH", "SOL", "BNB", "ADA"]}'::jsonb,
    "notification_settings" jsonb default '{"push": true, "email": true, "tradeExecuted": true, "signalDetected": true, "portfolioSummary": false}'::jsonb,
    "dark_mode" boolean default true,
    "created_at" timestamp with time zone default now(),
    "updated_at" timestamp with time zone default now()
);


alter table "public"."user_settings" enable row level security;

alter table "public"."posts" drop column "comments_count";

alter table "public"."posts" drop column "likes_count";

alter table "public"."posts" drop column "profile_id";

alter table "public"."posts" drop column "status";

alter table "public"."posts" add column "author" text not null default 'j.p_morgan_trading'::text;

alter table "public"."posts" add column "image_urls" jsonb default '[]'::jsonb;

alter table "public"."posts" alter column "created_at" set default now();

alter table "public"."posts" alter column "id" set default gen_random_uuid();

alter table "public"."posts" alter column "updated_at" set default now();

alter table "public"."posts" enable row level security;

alter table "public"."profiles" drop column "bio";

alter table "public"."profiles" drop column "display_name";

alter table "public"."profiles" drop column "profile_image_url";

alter table "public"."profiles" add column "avatar_url" text;

alter table "public"."profiles" add column "full_name" text;

alter table "public"."profiles" add column "role" text default 'user'::text;

alter table "public"."profiles" alter column "created_at" set default now();

alter table "public"."profiles" alter column "id" drop default;

alter table "public"."profiles" alter column "updated_at" set default now();

alter table "public"."profiles" alter column "username" drop not null;

alter table "public"."profiles" enable row level security;

drop type "public"."post_status";

CREATE INDEX posts_author_idx ON public.posts USING btree (author);

CREATE UNIQUE INDEX posts_content_posted_at_unique ON public.posts USING btree (content, posted_at);

CREATE UNIQUE INDEX user_settings_pkey ON public.user_settings USING btree (id);

CREATE INDEX posts_posted_at_idx ON public.posts USING btree (posted_at DESC);

alter table "public"."user_settings" add constraint "user_settings_pkey" PRIMARY KEY using index "user_settings_pkey";

alter table "public"."posts" add constraint "posts_content_posted_at_unique" UNIQUE using index "posts_content_posted_at_unique";

alter table "public"."profiles" add constraint "profiles_id_fkey" FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."profiles" validate constraint "profiles_id_fkey";

alter table "public"."profiles" add constraint "profiles_role_check" CHECK ((role = ANY (ARRAY['admin'::text, 'user'::text]))) not valid;

alter table "public"."profiles" validate constraint "profiles_role_check";

alter table "public"."user_settings" add constraint "user_settings_id_fkey" FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE not valid;

alter table "public"."user_settings" validate constraint "user_settings_id_fkey";

set check_function_bodies = off;

CREATE OR REPLACE FUNCTION public.handle_new_profile()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
  INSERT INTO public.user_settings (id)
  VALUES (NEW.id);
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.handle_new_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
BEGIN
  INSERT INTO public.profiles (id, username)
  VALUES (NEW.id, NEW.email);
  RETURN NEW;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$function$
;

grant delete on table "public"."user_settings" to "anon";

grant insert on table "public"."user_settings" to "anon";

grant references on table "public"."user_settings" to "anon";

grant select on table "public"."user_settings" to "anon";

grant trigger on table "public"."user_settings" to "anon";

grant truncate on table "public"."user_settings" to "anon";

grant update on table "public"."user_settings" to "anon";

grant delete on table "public"."user_settings" to "authenticated";

grant insert on table "public"."user_settings" to "authenticated";

grant references on table "public"."user_settings" to "authenticated";

grant select on table "public"."user_settings" to "authenticated";

grant trigger on table "public"."user_settings" to "authenticated";

grant truncate on table "public"."user_settings" to "authenticated";

grant update on table "public"."user_settings" to "authenticated";

grant delete on table "public"."user_settings" to "service_role";

grant insert on table "public"."user_settings" to "service_role";

grant references on table "public"."user_settings" to "service_role";

grant select on table "public"."user_settings" to "service_role";

grant trigger on table "public"."user_settings" to "service_role";

grant truncate on table "public"."user_settings" to "service_role";

grant update on table "public"."user_settings" to "service_role";

create policy "Authenticated can insert posts"
on "public"."posts"
as permissive
for insert
to authenticated
with check (true);


create policy "Authenticated can update posts"
on "public"."posts"
as permissive
for update
to authenticated
using (true);


create policy "Public can read posts"
on "public"."posts"
as permissive
for select
to public
using (true);


create policy "Admins can read all profiles"
on "public"."profiles"
as permissive
for select
to public
using (((auth.uid() = id) OR ((auth.jwt() ->> 'role'::text) = 'admin'::text)));


create policy "Admins can update all profiles"
on "public"."profiles"
as permissive
for update
to public
using (((auth.uid() = id) OR ((auth.jwt() ->> 'role'::text) = 'admin'::text)));


create policy "Users can read own profile"
on "public"."profiles"
as permissive
for select
to public
using ((auth.uid() = id));


create policy "Users can update own profile"
on "public"."profiles"
as permissive
for update
to public
using ((auth.uid() = id));


create policy "Admins can read all user settings"
on "public"."user_settings"
as permissive
for select
to public
using (((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = 'admin'::text)))) OR (auth.uid() = id)));


create policy "Admins can update all user settings"
on "public"."user_settings"
as permissive
for update
to public
using (((EXISTS ( SELECT 1
   FROM profiles
  WHERE ((profiles.id = auth.uid()) AND (profiles.role = 'admin'::text)))) OR (auth.uid() = id)));


create policy "Users can read own settings"
on "public"."user_settings"
as permissive
for select
to public
using ((auth.uid() = id));


create policy "Users can update own settings"
on "public"."user_settings"
as permissive
for update
to public
using ((auth.uid() = id));


CREATE TRIGGER on_profile_created AFTER INSERT ON public.profiles FOR EACH ROW EXECUTE FUNCTION handle_new_profile();


