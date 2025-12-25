--
-- PostgreSQL database dump
--

\restrict xXvou3UdGf2feyFFx4zuW2FlkwcLJduKFwnxNrs9jhfukLgglF9vfdLZNomZnaY

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: assets; Type: TABLE; Schema: public; Owner: ani
--

CREATE TABLE public.assets (
    id integer NOT NULL,
    symbol text NOT NULL,
    name text,
    type text,
    currency text DEFAULT 'usd'::text
);


ALTER TABLE public.assets OWNER TO ani;

--
-- Name: assets_id_seq; Type: SEQUENCE; Schema: public; Owner: ani
--

CREATE SEQUENCE public.assets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.assets_id_seq OWNER TO ani;

--
-- Name: assets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ani
--

ALTER SEQUENCE public.assets_id_seq OWNED BY public.assets.id;


--
-- Name: prices; Type: TABLE; Schema: public; Owner: ani
--

CREATE TABLE public.prices (
    id bigint NOT NULL,
    assetid integer NOT NULL,
    date date NOT NULL,
    close numeric,
    adjclose numeric,
    vol bigint
);


ALTER TABLE public.prices OWNER TO ani;

--
-- Name: prices_id_seq; Type: SEQUENCE; Schema: public; Owner: ani
--

CREATE SEQUENCE public.prices_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.prices_id_seq OWNER TO ani;

--
-- Name: prices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: ani
--

ALTER SEQUENCE public.prices_id_seq OWNED BY public.prices.id;


--
-- Name: assets id; Type: DEFAULT; Schema: public; Owner: ani
--

ALTER TABLE ONLY public.assets ALTER COLUMN id SET DEFAULT nextval('public.assets_id_seq'::regclass);


--
-- Name: prices id; Type: DEFAULT; Schema: public; Owner: ani
--

ALTER TABLE ONLY public.prices ALTER COLUMN id SET DEFAULT nextval('public.prices_id_seq'::regclass);


--
-- Name: assets assets_pkey; Type: CONSTRAINT; Schema: public; Owner: ani
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_pkey PRIMARY KEY (id);


--
-- Name: assets assets_symbol_key; Type: CONSTRAINT; Schema: public; Owner: ani
--

ALTER TABLE ONLY public.assets
    ADD CONSTRAINT assets_symbol_key UNIQUE (symbol);


--
-- Name: prices prices_assetid_date_key; Type: CONSTRAINT; Schema: public; Owner: ani
--

ALTER TABLE ONLY public.prices
    ADD CONSTRAINT prices_assetid_date_key UNIQUE (assetid, date);


--
-- Name: prices prices_pkey; Type: CONSTRAINT; Schema: public; Owner: ani
--

ALTER TABLE ONLY public.prices
    ADD CONSTRAINT prices_pkey PRIMARY KEY (id);


--
-- Name: prices prices_assetid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: ani
--

ALTER TABLE ONLY public.prices
    ADD CONSTRAINT prices_assetid_fkey FOREIGN KEY (assetid) REFERENCES public.assets(id) ON DELETE CASCADE;


--
-- Name: TABLE assets; Type: ACL; Schema: public; Owner: ani
--

GRANT ALL ON TABLE public.assets TO stocksim;


--
-- Name: SEQUENCE assets_id_seq; Type: ACL; Schema: public; Owner: ani
--

GRANT ALL ON SEQUENCE public.assets_id_seq TO stocksim;


--
-- Name: TABLE prices; Type: ACL; Schema: public; Owner: ani
--

GRANT ALL ON TABLE public.prices TO stocksim;


--
-- Name: SEQUENCE prices_id_seq; Type: ACL; Schema: public; Owner: ani
--

GRANT ALL ON SEQUENCE public.prices_id_seq TO stocksim;


--
-- PostgreSQL database dump complete
--

\unrestrict xXvou3UdGf2feyFFx4zuW2FlkwcLJduKFwnxNrs9jhfukLgglF9vfdLZNomZnaY

