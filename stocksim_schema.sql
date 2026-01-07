--
-- PostgreSQL database dump (Cleaned for Cloud Deployment)
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET search_path = public;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: assets; Type: TABLE; Schema: public
--

CREATE TABLE IF NOT EXISTS public.assets (
    id SERIAL PRIMARY KEY,
    symbol text NOT NULL UNIQUE,
    name text,
    type text,
    currency text DEFAULT 'usd'::text
);


--
-- Name: prices; Type: TABLE; Schema: public
--

CREATE TABLE IF NOT EXISTS public.prices (
    id SERIAL PRIMARY KEY,
    asset_id integer NOT NULL,
    date date NOT NULL,
    close numeric,
    adj_close numeric,
    volume bigint,
    CONSTRAINT prices_assetid_date_key UNIQUE (asset_id, date),
    CONSTRAINT prices_assetid_fkey FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE CASCADE
);

--
-- Indexes and Constraints (Implicitly created by SERIAL and UNIQUE above, but making sure)
--