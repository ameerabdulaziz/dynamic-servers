--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (84ade85)
-- Dumped by pg_dump version 17.5

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

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: user_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role AS ENUM (
    'admin',
    'technical_agent',
    'sales_agent'
);


--
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'TECHNICAL_AGENT',
    'SALES_AGENT'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: client_subscription; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_subscription (
    id integer NOT NULL,
    client_name character varying(100) NOT NULL,
    client_email character varying(120) NOT NULL,
    subscription_start date NOT NULL,
    subscription_end date NOT NULL,
    subscription_type character varying(50) NOT NULL,
    monthly_cost double precision NOT NULL,
    server_id integer,
    managed_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_active boolean,
    auto_renewal boolean
);


--
-- Name: client_subscription_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.client_subscription_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: client_subscription_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.client_subscription_id_seq OWNED BY public.client_subscription.id;


--
-- Name: database_backup; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.database_backup (
    id integer NOT NULL,
    backup_id character varying(36) NOT NULL,
    server_id integer NOT NULL,
    database_name character varying(100) NOT NULL,
    backup_type character varying(20) NOT NULL,
    backup_size bigint,
    backup_path character varying(255),
    compression_used boolean,
    encryption_used boolean,
    started_at timestamp without time zone NOT NULL,
    completed_at timestamp without time zone,
    status character varying(20),
    initiated_by integer NOT NULL,
    error_message text,
    retry_count integer,
    backup_log text,
    error_log text
);


--
-- Name: database_backup_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.database_backup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: database_backup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.database_backup_id_seq OWNED BY public.database_backup.id;


--
-- Name: deployment_execution; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_execution (
    id integer NOT NULL,
    execution_id character varying(36) NOT NULL,
    server_id integer NOT NULL,
    script_id integer NOT NULL,
    executed_by integer NOT NULL,
    status character varying(20),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    ansible_output text,
    error_log text,
    exit_code integer,
    execution_variables text
);


--
-- Name: deployment_execution_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.deployment_execution_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: deployment_execution_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.deployment_execution_id_seq OWNED BY public.deployment_execution.id;


--
-- Name: deployment_script; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deployment_script (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    ansible_playbook text NOT NULL,
    variables text,
    created_by integer NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    execution_count integer,
    last_executed timestamp without time zone
);


--
-- Name: deployment_script_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.deployment_script_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: deployment_script_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.deployment_script_id_seq OWNED BY public.deployment_script.id;


--
-- Name: hetzner_projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hetzner_projects (
    id integer NOT NULL,
    project_id character varying(20) NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    hetzner_api_token character varying(200) NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    created_by integer NOT NULL,
    max_servers integer,
    monthly_budget numeric(10,2),
    ssh_username character varying(50) DEFAULT 'root'::character varying,
    ssh_port integer DEFAULT 22,
    ssh_private_key text,
    ssh_public_key text,
    ssh_key_passphrase character varying(255),
    ssh_connection_tested boolean DEFAULT false,
    ssh_last_test timestamp without time zone,
    base_domain character varying(100)
);


--
-- Name: hetzner_projects_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.hetzner_projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hetzner_projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.hetzner_projects_id_seq OWNED BY public.hetzner_projects.id;


--
-- Name: hetzner_server; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hetzner_server (
    id integer NOT NULL,
    hetzner_id integer,
    name character varying(100) NOT NULL,
    status character varying(20) NOT NULL,
    server_type character varying(50) NOT NULL,
    image character varying(100),
    public_ip character varying(15),
    private_ip character varying(15),
    ipv6 character varying(39),
    datacenter character varying(50),
    location character varying(50),
    cpu_cores integer,
    memory_gb double precision,
    disk_gb integer,
    created_at timestamp without time zone,
    last_synced timestamp without time zone,
    managed_by integer,
    deployment_status character varying(20),
    deployment_log text,
    last_deployment timestamp without time zone,
    project_id integer,
    reverse_dns character varying(255),
    server_source character varying(20) DEFAULT 'hetzner'::character varying NOT NULL,
    client_name character varying(100),
    client_contact character varying(255)
);


--
-- Name: hetzner_server_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.hetzner_server_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hetzner_server_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.hetzner_server_id_seq OWNED BY public.hetzner_server.id;


--
-- Name: notification; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notification (
    id integer NOT NULL,
    user_id integer NOT NULL,
    title character varying(200) NOT NULL,
    message text NOT NULL,
    type character varying(20),
    is_read boolean,
    created_at timestamp without time zone,
    request_id integer
);


--
-- Name: notification_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.notification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: notification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.notification_id_seq OWNED BY public.notification.id;


--
-- Name: server_request; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.server_request (
    id integer NOT NULL,
    request_id character varying(36) NOT NULL,
    user_id integer NOT NULL,
    server_name character varying(100) NOT NULL,
    server_type character varying(50) NOT NULL,
    cpu_cores integer NOT NULL,
    memory_gb integer NOT NULL,
    storage_gb integer NOT NULL,
    operating_system character varying(50) NOT NULL,
    application_name character varying(100),
    application_type character varying(50),
    application_description text,
    business_justification text,
    estimated_usage character varying(50) NOT NULL,
    status character varying(20),
    priority character varying(10),
    created_at timestamp without time zone,
    reviewed_at timestamp without time zone,
    deployed_at timestamp without time zone,
    reviewed_by integer,
    admin_notes text,
    deployment_notes text,
    server_ip character varying(15),
    deployment_progress integer,
    client_name character varying(100),
    project_id integer,
    subdomain character varying(100)
);


--
-- Name: server_request_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.server_request_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: server_request_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.server_request_id_seq OWNED BY public.server_request.id;


--
-- Name: system_update; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.system_update (
    id integer NOT NULL,
    update_id character varying(36) NOT NULL,
    server_id integer NOT NULL,
    update_type character varying(30) NOT NULL,
    update_description text NOT NULL,
    packages_updated text,
    kernel_update boolean,
    reboot_required boolean,
    reboot_completed boolean,
    scheduled_at timestamp without time zone,
    started_at timestamp without time zone NOT NULL,
    completed_at timestamp without time zone,
    status character varying(20),
    initiated_by integer NOT NULL,
    approved_by integer,
    pre_update_snapshot character varying(255),
    rollback_available boolean,
    rollback_completed boolean,
    error_message text,
    rollback_reason text,
    execution_log text,
    error_log text
);


--
-- Name: system_update_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.system_update_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: system_update_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.system_update_id_seq OWNED BY public.system_update.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(256) NOT NULL,
    role public.userrole NOT NULL,
    active boolean,
    created_at timestamp without time zone,
    is_manager boolean DEFAULT false,
    is_approved boolean DEFAULT true,
    profile_image character varying(200)
);


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: user_project_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_project_access (
    id integer NOT NULL,
    user_id integer NOT NULL,
    project_id integer NOT NULL,
    access_level character varying(20) DEFAULT 'read'::character varying,
    granted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    granted_by integer
);


--
-- Name: user_project_access_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_project_access_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_project_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_project_access_id_seq OWNED BY public.user_project_access.id;


--
-- Name: user_server_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_server_access (
    id integer NOT NULL,
    user_id integer NOT NULL,
    server_id integer NOT NULL,
    access_level character varying(20),
    assigned_at timestamp without time zone,
    assigned_by integer
);


--
-- Name: user_server_access_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_server_access_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_server_access_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_server_access_id_seq OWNED BY public.user_server_access.id;


--
-- Name: client_subscription id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_subscription ALTER COLUMN id SET DEFAULT nextval('public.client_subscription_id_seq'::regclass);


--
-- Name: database_backup id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_backup ALTER COLUMN id SET DEFAULT nextval('public.database_backup_id_seq'::regclass);


--
-- Name: deployment_execution id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_execution ALTER COLUMN id SET DEFAULT nextval('public.deployment_execution_id_seq'::regclass);


--
-- Name: deployment_script id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_script ALTER COLUMN id SET DEFAULT nextval('public.deployment_script_id_seq'::regclass);


--
-- Name: hetzner_projects id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_projects ALTER COLUMN id SET DEFAULT nextval('public.hetzner_projects_id_seq'::regclass);


--
-- Name: hetzner_server id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_server ALTER COLUMN id SET DEFAULT nextval('public.hetzner_server_id_seq'::regclass);


--
-- Name: notification id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification ALTER COLUMN id SET DEFAULT nextval('public.notification_id_seq'::regclass);


--
-- Name: server_request id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.server_request ALTER COLUMN id SET DEFAULT nextval('public.server_request_id_seq'::regclass);


--
-- Name: system_update id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_update ALTER COLUMN id SET DEFAULT nextval('public.system_update_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: user_project_access id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_project_access ALTER COLUMN id SET DEFAULT nextval('public.user_project_access_id_seq'::regclass);


--
-- Name: user_server_access id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_server_access ALTER COLUMN id SET DEFAULT nextval('public.user_server_access_id_seq'::regclass);


--
-- Data for Name: client_subscription; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.client_subscription (id, client_name, client_email, subscription_start, subscription_end, subscription_type, monthly_cost, server_id, managed_by, created_at, updated_at, is_active, auto_renewal) FROM stdin;
\.


--
-- Data for Name: database_backup; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.database_backup (id, backup_id, server_id, database_name, backup_type, backup_size, backup_path, compression_used, encryption_used, started_at, completed_at, status, initiated_by, error_message, retry_count, backup_log, error_log) FROM stdin;
1	ad523c2d-97c9-4173-980a-e9334a181537	9	main	full	\N	\N	t	t	2025-08-27 14:00:24.826513	2025-08-27 14:00:28.827786	completed	2	\N	0	Processed 2888 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2890 pages in 0.145 seconds (155.684 MB/sec).\n	\N
2	86ce2301-8394-4bb7-becf-e526704dafc9	9	main	full	\N	\N	t	t	2025-08-27 14:19:52.372275	2025-08-27 14:19:56.690946	completed	2	\N	0	Processed 2888 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2890 pages in 0.173 seconds (130.486 MB/sec).\n	\N
3	5fbe74a6-e745-45a1-8046-5145e9642730	11	main	full	\N	\N	t	t	2025-08-27 16:24:43.428184	2025-08-27 16:24:44.309787	failed	1	\N	0	\N	No SSH private key configured for this project. Please configure SSH access in project settings.
4	c8af0fad-ed66-4a5d-a007-b30750d26e44	11	main	full	\N	\N	t	t	2025-08-27 16:25:03.452779	2025-08-27 16:25:04.316443	failed	1	\N	0	\N	No SSH private key configured for this project. Please configure SSH access in project settings.
5	947a51b0-b4eb-4c74-805e-7139d9c740cc	9	main	full	\N	\N	t	t	2025-08-28 12:47:47.174639	2025-08-28 12:47:51.457525	completed	4	\N	0	Processed 2896 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2898 pages in 0.158 seconds (143.270 MB/sec).\n	\N
6	52b3d0c2-a1e1-4837-a760-a548385a49b6	9	main	full	\N	\N	t	t	2025-08-28 12:52:31.379555	2025-08-28 12:52:35.702858	completed	4	\N	0	Processed 2896 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2898 pages in 0.201 seconds (112.620 MB/sec).\n	\N
7	40a86158-ba76-4d61-a145-ae6633c7b247	9	main	full	\N	\N	t	t	2025-08-28 12:55:21.302247	2025-08-28 12:55:25.472125	completed	4	\N	0	Processed 2896 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2898 pages in 0.185 seconds (122.360 MB/sec).\n	\N
8	779c0754-851d-48ce-9365-15755a95e4ab	14	main	full	\N	\N	t	t	2025-08-28 13:00:53.182017	2025-08-28 13:00:57.766714	completed	4	\N	0	Processed 5672 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 5674 pages in 0.258 seconds (171.799 MB/sec).\n	\N
9	89f7403f-83ed-4aeb-8d5a-5dfef8e79c15	9	main	full	\N	\N	t	t	2025-08-28 13:19:33.979615	2025-08-28 13:19:38.248819	completed	4	\N	0	Processed 2896 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2898 pages in 0.182 seconds (124.377 MB/sec).\n	\N
10	fc5e3c0d-5426-4115-b050-5020d5360edd	2	main	full	\N	\N	t	t	2025-08-28 13:21:55.793792	2025-08-28 13:21:59.898331	completed	4	\N	0	Processed 16368 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 16370 pages in 0.369 seconds (346.576 MB/sec).\n	\N
11	b92578d4-5ff6-4156-900c-58bb03bf2be2	14	main	full	\N	\N	t	t	2025-08-28 13:22:15.570793	2025-08-28 13:22:19.829043	completed	4	\N	0	Processed 5672 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 5674 pages in 0.249 seconds (178.008 MB/sec).\n	\N
12	99ae64b0-9fd8-40c5-9908-a37a1fc93a24	14	main	full	\N	\N	t	t	2025-08-28 13:25:54.284824	2025-08-28 13:25:58.710326	completed	4	\N	0	Processed 5672 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 5674 pages in 0.272 seconds (162.956 MB/sec).\n	\N
13	573b1e59-d765-4eaa-88a1-2f20bb37d94c	14	main	full	\N	\N	t	t	2025-08-28 13:26:30.272672	2025-08-28 13:26:34.083205	completed	4	\N	0	Processed 5672 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 5674 pages in 0.253 seconds (175.194 MB/sec).\n	\N
14	d9525038-edd7-4aee-bccc-bc939512e7df	14	main	full	\N	\N	t	t	2025-08-28 13:26:54.530855	2025-08-28 13:26:58.252864	completed	4	\N	0	Processed 5672 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 5674 pages in 0.234 seconds (189.419 MB/sec).\n	\N
15	6367b4f1-eb63-42c4-b200-34b98839e1d7	14	main	full	\N	\N	t	t	2025-08-28 13:31:14.258718	2025-08-28 13:31:18.508598	completed	4	\N	0	Processed 5672 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 5674 pages in 0.255 seconds (173.820 MB/sec).\n	\N
16	d4eab980-c618-42cd-be01-b58a3b21aa35	9	main	full	\N	\N	t	t	2025-08-28 13:36:07.492913	2025-08-28 13:36:11.586478	completed	5	\N	0	Processed 2896 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2898 pages in 0.198 seconds (114.326 MB/sec).\n	\N
17	dc71bbdf-f888-4d05-8a7f-a2f2cb841fd9	1	main	full	\N	\N	t	t	2025-08-28 13:37:02.225732	2025-08-28 13:37:06.561033	completed	5	\N	0	Processed 24912 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 24914 pages in 0.333 seconds (584.494 MB/sec).\n	\N
18	69807db1-0b66-45b4-85c0-7542b2ca516c	9	main	full	\N	\N	t	t	2025-08-28 13:40:35.220366	2025-08-28 13:40:39.463811	completed	5	\N	0	Processed 2896 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2898 pages in 0.197 seconds (114.907 MB/sec).\n	\N
19	9c841e7d-3175-4f63-9eb3-2dab8ad3114b	1	main	full	\N	\N	t	t	2025-08-28 13:48:14.725696	2025-08-28 13:48:18.268487	completed	5	\N	0	Processed 24912 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 24914 pages in 0.279 seconds (697.622 MB/sec).\n	\N
20	3ed3157d-2b04-43ea-8e2e-2dffff63d0b3	11	main	full	6651904	static/backups/servers/technosat/technosat_backup_2025-09-09_01-52.bak	t	t	2025-09-08 22:52:39.939969	2025-09-08 22:52:44.773442	completed	1	\N	0	Processed 5688 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 5690 pages in 0.190 seconds (233.943 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001  6651904 Sep  9 01:52 technosat_backup_2025-09-09_01-52.bak\n	\N
21	7ece62f1-54bf-44e7-a923-89799eeff0c6	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_14-07.bak	t	t	2025-09-09 11:07:37.750242	2025-09-09 11:07:41.922213	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.134 seconds (170.329 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 14:07 test_backup_2025-09-09_14-07.bak\n	\N
22	9a108d00-1068-4bf5-bfc2-5230223f3f4e	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_14-14.bak	t	t	2025-09-09 11:14:35.975438	2025-09-09 11:14:39.517538	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.147 seconds (155.266 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 14:14 test_backup_2025-09-09_14-14.bak\n	\N
23	3d02e423-92ff-4568-9799-2d85ae9f2940	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_14-20.bak	t	t	2025-09-09 11:20:01.691585	2025-09-09 11:20:05.735799	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.144 seconds (158.501 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 14:20 test_backup_2025-09-09_14-20.bak\n	\N
24	bdd06721-81dc-4bcc-b242-156a84505026	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_14-32.bak	t	t	2025-09-09 11:32:36.144725	2025-09-09 11:32:40.365334	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.151 seconds (151.153 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 14:32 test_backup_2025-09-09_14-32.bak\n	\N
25	09cf8722-be66-4ed7-9d00-0c1fec6e54cc	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_15-00.bak	t	t	2025-09-09 12:00:30.732899	2025-09-09 12:00:34.884933	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.135 seconds (169.068 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 15:00 test_backup_2025-09-09_15-00.bak\n	\N
26	6fcde9d6-9b75-4dc9-8c9e-3fabdedad1c4	6	main	full	6152192	static/backups/servers/inspire/inspire_backup_2025-09-09_15-00.bak	t	t	2025-09-09 12:00:42.513853	2025-09-09 12:00:47.054779	completed	5	\N	0	Processed 4048 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 4050 pages in 0.208 seconds (152.099 MB/sec).\nBACKUP_COMPLETED\n-rwxrwxr-x 1 dynamic dynamic 32624128 Apr 22 23:58 nova_hr.bak\n	\N
27	a90f34a6-d443-4cfd-9a70-1833429a62b4	6	main	full	6152192	static/backups/servers/inspire/inspire_backup_2025-09-09_15-01.bak	t	t	2025-09-09 12:01:16.983637	2025-09-09 12:01:20.632706	completed	5	\N	0	Processed 4048 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 4050 pages in 0.150 seconds (210.911 MB/sec).\nBACKUP_COMPLETED\n-rwxrwxr-x 1 dynamic dynamic 32624128 Apr 22 23:58 nova_hr.bak\n	\N
28	6f7368f4-b800-4836-bbbf-508b2140fed1	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_15-04.bak	t	t	2025-09-09 12:04:21.878611	2025-09-09 12:04:26.101664	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.180 seconds (126.801 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 15:04 test_backup_2025-09-09_15-04.bak\n	\N
29	476f1e13-bfb5-47be-81b2-8db3d94fff8a	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_15-13.bak	t	t	2025-09-09 12:13:15.492821	2025-09-09 12:13:18.812201	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.159 seconds (143.548 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 15:13 test_backup_2025-09-09_15-13.bak\n	\N
30	706a1e79-a6fe-4101-aa72-d585c0626302	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_16-18.bak	t	t	2025-09-09 13:18:03.909169	2025-09-09 13:18:08.12254	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.180 seconds (126.801 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 16:18 test_backup_2025-09-09_16-18.bak\n	\N
31	99abed0d-8374-4fd7-bbb5-92f4215d2718	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_16-20.bak	t	t	2025-09-09 13:20:46.972279	2025-09-09 13:20:51.355365	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.183 seconds (124.722 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 16:20 test_backup_2025-09-09_16-20.bak\n	\N
32	16909739-e8bb-4b77-b3b8-893a4684fb8a	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_16-25.bak	t	t	2025-09-09 13:25:41.105982	2025-09-09 13:25:44.69428	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.162 seconds (140.890 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 16:25 test_backup_2025-09-09_16-25.bak\n	\N
33	562c2d2c-f552-4780-947f-e1307ab5260f	9	main	full	5005312	static/backups/servers/nova-hr-test/test_backup_2025-09-09_16-27.bak	t	t	2025-09-09 13:27:37.268717	2025-09-09 13:27:41.538751	completed	5	\N	0	Processed 2920 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 2922 pages in 0.172 seconds (132.698 MB/sec).\nBACKUP_COMPLETED\n-rw-r--r-- 1   10001   10001 5005312 Sep  9 16:27 test_backup_2025-09-09_16-27.bak\n	\N
34	7ba58efb-0402-42f5-91c4-f71a032e26cf	51	main	full	\N	\N	t	t	2025-09-10 13:38:45.295529	2025-09-10 13:38:46.0177	skipped	1	\N	0	\N	Backup operations are not currently available for self-hosted servers. Please manage backups directly on the client server.
35	9133f625-5164-4c72-a6f7-b26b971590f2	51	main	full	\N	\N	t	t	2025-09-10 14:02:33.365725	2025-09-10 14:02:34.104284	skipped	1	\N	0	\N	Backup operations are not currently available for self-hosted servers. Please manage backups directly on the client server.
36	9cd0f139-e26a-4f03-8e5b-fac2e6b042d0	51	main	full	18986496	static/backups/servers/mvls/nova_hr.bak	t	t	2025-09-10 15:21:31.541866	2025-09-10 15:21:34.767255	completed	1	\N	0	Msg 3201, Level 16, State 1, Server 86c3d2a6b2c2, Line 1\nCannot open backup device '/var/opt/mssql/backup/mvls_backup_2025-09-10_18-21.bak'. Operating system error 5(Access is denied.).\nMsg 3013, Level 16, State 1, Server 86c3d2a6b2c2, Line 1\nBACKUP DATABASE is terminating abnormally.\nBACKUP_COMPLETED\n-rw-rw-r-- 1   10001 dynamic 18986496 Jul  8 18:53 nova_hr.bak\n	\N
37	f60f695c-7040-457b-8389-b1c40d55de50	52	main	full	4501504	static/backups/servers/decarbon/decarbon_backup_2025-09-11_20-06.bak	t	t	2025-09-11 17:05:58.384942	2025-09-11 17:06:03.002201	completed	5	\N	0	Processed 3008 pages for database 'nova_hr', file 'Payroll1' on file 1.\nProcessed 2 pages for database 'nova_hr', file 'Payroll1_log' on file 1.\nBACKUP DATABASE successfully processed 3010 pages in 0.114 seconds (206.243 MB/sec).\nBACKUP_COMPLETED\n-rwxrwxr-x 1   10001   10001 24272896 Sep 11 16:29 nova_hr.bak\n	\N
\.


--
-- Data for Name: deployment_execution; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.deployment_execution (id, execution_id, server_id, script_id, executed_by, status, started_at, completed_at, ansible_output, error_log, exit_code, execution_variables) FROM stdin;
\.


--
-- Data for Name: deployment_script; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.deployment_script (id, name, description, ansible_playbook, variables, created_by, created_at, updated_at, execution_count, last_executed) FROM stdin;
\.


--
-- Data for Name: hetzner_projects; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hetzner_projects (id, project_id, name, description, hetzner_api_token, is_active, created_at, updated_at, created_by, max_servers, monthly_budget, ssh_username, ssh_port, ssh_private_key, ssh_public_key, ssh_key_passphrase, ssh_connection_tested, ssh_last_test, base_domain) FROM stdin;
3	PRJCFB5FA17	Django Projects	Development and staging environment for Django-based web applications and API services	USE_ENV_TOKEN	f	2025-08-27 11:28:54.552061	2025-08-27 11:28:54.552066	1	15	500.00	root	22	\N	\N	\N	f	\N	django.dynamicservers.io
2	PRJB04B92B7	Frappe ERP	Enterprise Resource Planning system with CRM, accounting, inventory, and project management modules	UB2Yxpc4PncoRz40pdyza8BTkASpb2gBOvLIqDx1iMJBb5We6trzpBpqpDzf8RkH	t	2025-08-27 11:28:54.264775	2025-09-02 14:54:32.999017	1	100	500.00	root	22	\N	\N	\N	f	\N	erp.dynamicservers.io
1	PRJAAAE7800	Nova HR	Human Resources management platform with employee onboarding, payroll, and performance tracking systems	XI2WWI08YXZYgZzIAWKs7C7cN5Q3vscmP5tnEsjoof5Vg6XXsAhKgKExGvk3cnNk	t	2025-08-27 11:28:53.962701	2025-09-02 14:33:05.002461	1	100	500.00	dynamic	22	-----BEGIN OPENSSH PRIVATE KEY-----\r\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW\r\nQyNTUxOQAAACDLh6oftMV8xx/PQ3iKmMyMpXG/dKQTAxnQT8DvLMDxbwAAAJgkkdOaJJHT\r\nmgAAAAtzc2gtZWQyNTUxOQAAACDLh6oftMV8xx/PQ3iKmMyMpXG/dKQTAxnQT8DvLMDxbw\r\nAAAECkzw8GvkjVQgJsHrKlQMmJoVxFyaroBfvgD5gGSDTQHsuHqh+0xXzHH89DeIqYzIyl\r\ncb90pBMDGdBPwO8swPFvAAAAFGFtZWVyQHByZWNpc2lvbi03NzIwAQ==\r\n-----END OPENSSH PRIVATE KEY-----	ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMuHqh+0xXzHH89DeIqYzIylcb90pBMDGdBPwO8swPFv ameer@precision-7720		t	2025-08-27 13:48:35.853587	novahrs.com
\.


--
-- Data for Name: hetzner_server; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hetzner_server (id, hetzner_id, name, status, server_type, image, public_ip, private_ip, ipv6, datacenter, location, cpu_cores, memory_gb, disk_gb, created_at, last_synced, managed_by, deployment_status, deployment_log, last_deployment, project_id, reverse_dns, server_source, client_name, client_contact) FROM stdin;
26	62485552	maged-zytoon	running	cpx21	ubuntu-22.04	91.99.50.160	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-09-02 14:54:48.001814	2025-09-02 14:54:47.998412	\N	none	\N	\N	2	static.160.50.99.91.clients.your-server.de	hetzner	\N	\N
27	62485554	artal-ksa	running	cpx21	ubuntu-22.04	91.99.59.27	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-09-02 14:54:48.311065	2025-09-02 14:54:48.31012	\N	none	\N	\N	2	static.27.59.99.91.clients.your-server.de	hetzner	\N	\N
28	62485555	nks-ksa	running	cpx21	ubuntu-22.04	91.99.59.28	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-09-02 14:54:48.601055	2025-09-02 14:54:48.599907	\N	none	\N	\N	2	static.28.59.99.91.clients.your-server.de	hetzner	\N	\N
29	62485557	material-composites	running	cpx21	ubuntu-22.04	91.99.48.247	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-09-02 14:54:48.888605	2025-09-02 14:54:48.887781	\N	none	\N	\N	2	static.247.48.99.91.clients.your-server.de	hetzner	\N	\N
30	63602479	egyptian-porcelain	running	cx42	ubuntu-22.04	157.180.69.154	\N	\N	hel1-dc2	hel1	8	16	160	2025-09-02 14:54:49.183695	2025-09-02 14:54:49.182532	\N	none	\N	\N	2	static.154.69.180.157.clients.your-server.de	hetzner	\N	\N
31	63642934	terra	running	cx42	ubuntu-22.04	78.46.242.2	\N	\N	nbg1-dc3	nbg1	8	16	160	2025-09-02 14:54:49.474578	2025-09-02 14:54:49.473378	\N	none	\N	\N	2	static.2.242.46.78.clients.your-server.de	hetzner	\N	\N
32	63794712	olive-roots	running	cx32	unknown	37.27.246.4	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:49.765432	2025-09-02 14:54:49.764304	\N	none	\N	\N	2	static.4.246.27.37.clients.your-server.de	hetzner	\N	\N
33	64751173	layalmed	running	cx32	ubuntu-22.04	91.99.77.117	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-09-02 14:54:50.055265	2025-09-02 14:54:50.053647	\N	none	\N	\N	2	static.117.77.99.91.clients.your-server.de	hetzner	\N	\N
34	64851222	united-lamp	running	cx32	ubuntu-22.04	157.180.127.229	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:50.343655	2025-09-02 14:54:50.342177	\N	none	\N	\N	2	static.229.127.180.157.clients.your-server.de	hetzner	\N	\N
35	65472968	siwar	running	cpx41	unknown	135.181.38.187	\N	\N	hel1-dc2	hel1	8	16	240	2025-09-02 14:54:50.631406	2025-09-02 14:54:50.630044	\N	none	\N	\N	2	static.187.38.181.135.clients.your-server.de	hetzner	\N	\N
36	65574992	riyada	running	cpx41	ubuntu-22.04	157.180.20.186	\N	\N	hel1-dc2	hel1	8	16	240	2025-09-02 14:54:50.922412	2025-09-02 14:54:50.92129	\N	none	\N	\N	2	static.186.20.180.157.clients.your-server.de	hetzner	\N	\N
37	65822289	egyphar	running	cx32	ubuntu-22.04	46.62.141.197	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:51.211828	2025-09-02 14:54:51.21077	\N	none	\N	\N	2	static.197.141.62.46.clients.your-server.de	hetzner	\N	\N
38	65881613	ams	running	cx32	ubuntu-22.04	157.180.117.136	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:51.500771	2025-09-02 14:54:51.499859	\N	none	\N	\N	2	static.136.117.180.157.clients.your-server.de	hetzner	\N	\N
39	103186466	blue-shield	running	cx32	ubuntu-22.04	65.108.144.224	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:51.790632	2025-09-02 14:54:51.789266	\N	none	\N	\N	2	static.224.144.108.65.clients.your-server.de	hetzner	\N	\N
40	104832283	light-fast	running	cx32	ubuntu-22.04	46.62.172.83	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:52.087338	2025-09-02 14:54:52.086303	\N	none	\N	\N	2	static.83.172.62.46.clients.your-server.de	hetzner	\N	\N
41	105028370	enjaz	running	cx42	ubuntu-22.04	157.180.77.244	\N	\N	hel1-dc2	hel1	8	16	160	2025-09-02 14:54:52.376773	2025-09-02 14:54:52.375812	\N	none	\N	\N	2	static.244.77.180.157.clients.your-server.de	hetzner	\N	\N
42	105960901	frappe-erp-test	running	cx32	ubuntu-22.04	157.180.89.33	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:52.665823	2025-09-02 14:54:52.664898	\N	none	\N	\N	2	static.33.89.180.157.clients.your-server.de	hetzner	\N	\N
43	105960925	frappe-erp-demo-ksa	running	cx32	ubuntu-22.04	65.21.253.14	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:52.954651	2025-09-02 14:54:52.953727	\N	none	\N	\N	2	static.14.253.21.65.clients.your-server.de	hetzner	\N	\N
44	105960991	frappe-erp-demo	running	cx32	ubuntu-22.04	65.109.229.92	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:53.244307	2025-09-02 14:54:53.243346	\N	none	\N	\N	2	static.92.229.109.65.clients.your-server.de	hetzner	\N	\N
45	106465675	test-ansible	running	cx32	ubuntu-22.04	95.216.216.98	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:53.534328	2025-09-02 14:54:53.533434	\N	none	\N	\N	2	static.98.216.216.95.clients.your-server.de	hetzner	\N	\N
46	106595239	elevanastore	running	cx32	ubuntu-22.04	65.21.243.120	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:53.823342	2025-09-02 14:54:53.822391	\N	none	\N	\N	2	static.120.243.21.65.clients.your-server.de	hetzner	\N	\N
47	106675341	kmina	running	cx32	ubuntu-22.04	37.27.32.85	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:54.111768	2025-09-02 14:54:54.11092	\N	none	\N	\N	2	static.85.32.27.37.clients.your-server.de	hetzner	\N	\N
48	107525809	frappe-erp-invoices	running	cx32	ubuntu-22.04	135.181.43.118	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-02 14:54:54.400647	2025-09-02 14:54:54.399992	\N	none	\N	\N	2	static.118.43.181.135.clients.your-server.de	hetzner	\N	\N
22	62424141	material-composites	running	cpx21	docker-ce	49.13.146.88	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-09-02 14:15:30.129268	2025-09-02 17:15:53.368217	\N	none	\N	\N	1	static.88.146.13.49.clients.your-server.de	hetzner	\N	\N
23	62424146	al-hudaif	running	cpx31	docker-ce	91.99.24.127	\N	\N	nbg1-dc3	nbg1	4	8	160	2025-09-02 14:15:30.426779	2025-09-02 17:15:53.664865	\N	none	\N	\N	1	static.127.24.99.91.clients.your-server.de	hetzner	\N	\N
1	62483369	sabahy	running	cpx21	docker-ce	78.46.216.107	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-08-27 12:08:44.068947	2025-09-02 17:15:53.960947	\N	none	\N	\N	1	static.107.216.46.78.clients.your-server.de	hetzner	\N	\N
2	62483982	ehaf	running	cpx21	docker-ce	91.99.54.0	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-08-27 12:08:44.370255	2025-09-02 17:15:54.251803	\N	none	\N	\N	1	static.0.54.99.91.clients.your-server.de	hetzner	\N	\N
3	62731319	world-aviation	running	cpx21	docker-ce	91.99.73.182	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-08-27 12:08:44.660892	2025-09-02 17:15:54.541844	\N	none	\N	\N	1	static.182.73.99.91.clients.your-server.de	hetzner	\N	\N
4	62880147	delta-el-nile	running	cx32	docker-ce	138.199.194.67	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:44.948799	2025-09-02 17:15:54.835396	\N	none	\N	\N	1	static.67.194.199.138.clients.your-server.de	hetzner	\N	\N
5	62880148	ecip	running	cx32	docker-ce	167.235.136.56	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:45.256048	2025-09-02 17:15:55.123845	\N	none	\N	\N	1	static.56.136.235.167.clients.your-server.de	hetzner	\N	\N
6	63231869	inspire	running	cx32	docker-ce	91.99.20.203	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:45.547047	2025-09-02 17:15:55.700733	\N	none	\N	\N	1	static.203.20.99.91.clients.your-server.de	hetzner	\N	\N
7	63231871	mokambo	running	cx32	docker-ce	162.55.62.13	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:45.835313	2025-09-02 17:15:56.290493	\N	none	\N	\N	1	static.13.62.55.162.clients.your-server.de	hetzner	\N	\N
9	64052824	nova-hr-test	running	cx32	docker-ce	168.119.249.64	\N	\N	fsn1-dc14	fsn1	4	8	80	2025-08-27 12:08:46.421082	2025-09-08 21:54:25.660077	\N	none	\N	\N	1	test.novahrs.com	hetzner	\N	\N
24	63231868	riyada	running	cx32	docker-ce	116.203.244.126	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-09-02 14:15:31.430111	2025-09-08 22:40:48.162415	\N	none	\N	\N	1	riyada.novahrs.com	hetzner	\N	\N
25	63231870	oliveroots	running	cx32	docker-ce	195.201.98.229	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-09-02 14:15:31.8599	2025-09-08 22:40:48.600623	\N	none	\N	\N	1	oliveroots.novahrs.com	hetzner	\N	\N
8	63894842	petronas	running	cx32	docker-ce	138.199.221.171	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:46.132898	2025-09-08 22:40:49.030009	\N	none	\N	\N	1	petronas.novahrs.com	hetzner	\N	\N
11	100739667	technosat	running	cx32	docker-ce	95.216.219.177	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.005951	2025-09-08 22:40:49.458581	\N	none	\N	\N	1	tecnosat.novahrs.com	hetzner	\N	\N
12	103163473	spc	running	cx32	docker-ce	65.108.213.57	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.295771	2025-09-08 22:40:49.744143	\N	none	\N	\N	1	spc.novahrs.com	hetzner	\N	\N
13	103190743	dynamic	running	cx32	docker-ce	46.62.129.242	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.584269	2025-09-08 22:40:50.030301	\N	none	\N	\N	1	dynamic.novahrs.com	hetzner	\N	\N
14	103890656	hamam-abdo	running	cx32	docker-ce	157.180.84.86	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.872042	2025-09-08 22:40:50.316629	\N	none	\N	\N	1	hamam-abdo.novahrs.com	hetzner	\N	\N
51	\N	mvls	running	VPS-4GB		37.148.203.249		\N			4	8	80	2025-09-10 13:36:47.49373	2025-09-10 13:36:47.493733	1	none	\N	\N	1	mvls.novahrs.com	self_hosted	MVLS	mvls@test.com
15	105385555	rtx	running	cx22	docker-ce	95.216.138.122	\N	\N	hel1-dc2	hel1	2	4	40	2025-08-27 12:08:48.164152	2025-09-08 17:45:33.315498	\N	none	\N	\N	1	rtx.novahrs.com	hetzner	\N	\N
49	108269536	al-hudaif	running	cx32	ubuntu-22.04	37.27.81.142	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-08 17:55:25.533373	2025-09-08 17:55:25.530889	\N	none	\N	\N	2	static.142.81.27.37.clients.your-server.de	hetzner	\N	\N
50	108269549	nutrity	running	cx32	ubuntu-22.04	37.27.240.167	\N	\N	hel1-dc2	hel1	4	8	80	2025-09-08 17:55:25.833051	2025-09-08 17:55:25.832138	\N	none	\N	\N	2	static.167.240.27.37.clients.your-server.de	hetzner	\N	\N
52	\N	decarbon	running	Client-Managed	\N	158.220.94.206	158.220.94.206	\N	\N	\N	\N	\N	\N	2025-09-11 16:42:00.566486	2025-09-11 17:11:06.25899	5	none	\N	\N	1	158.220.94.206	self_hosted	Decarbon	decarbon@test.com
\.


--
-- Data for Name: notification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notification (id, user_id, title, message, type, is_read, created_at, request_id) FROM stdin;
1	8	Server Request Submitted	Your server request for "Test Request" (server: test-request) has been submitted and is pending approval.	info	f	2025-09-02 19:49:06.652698	2
2	8	Server Request Approved	Your server request "test-request" has been approved.	success	f	2025-09-02 20:02:23.919645	2
\.


--
-- Data for Name: server_request; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.server_request (id, request_id, user_id, server_name, server_type, cpu_cores, memory_gb, storage_gb, operating_system, application_name, application_type, application_description, business_justification, estimated_usage, status, priority, created_at, reviewed_at, deployed_at, reviewed_by, admin_notes, deployment_notes, server_ip, deployment_progress, client_name, project_id, subdomain) FROM stdin;
2	4cecc0b4-6033-4b1e-ac95-dd72a7726223	8	test-request	cx21	2	4	40	ubuntu-22.04	\N	\N	\N		low	approved	medium	2025-09-02 19:49:05.766865	2025-09-02 20:02:23.761655	\N	1		\N	\N	0	Test Request	1	test-request
\.


--
-- Data for Name: system_update; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.system_update (id, update_id, server_id, update_type, update_description, packages_updated, kernel_update, reboot_required, reboot_completed, scheduled_at, started_at, completed_at, status, initiated_by, approved_by, pre_update_snapshot, rollback_available, rollback_completed, error_message, rollback_reason, execution_log, error_log) FROM stdin;
1	4b8e848c-b6bb-4392-911b-ad0b1f3d62f0	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-08-27 12:42:22.149151	2025-08-27 12:42:22.466289	failed	2	\N	\N	f	f	\N	\N	\N	\N
2	790a5379-7454-4155-82e4-4b1cba7d0c09	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-08-27 13:04:53.552197	2025-08-27 13:05:17.160896	completed	2	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 52 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
3	aacd61e5-0e8e-473c-aafc-a068047d4df9	1	deployment	Testing Nova HR Docker deployment script execution via SSH	\N	f	f	f	\N	2025-08-27 13:15:11.549843	\N	running	1	\N	\N	f	f	\N	\N	\N	\N
4	4b8a6e92-4168-4967-9d1b-c4aa584f3b29	1	deployment	Testing Nova HR Docker deployment script execution via SSH	\N	f	f	f	\N	2025-08-27 13:15:35.463717	2025-08-27 13:15:36.19938	failed	1	\N	\N	f	f	\N	\N	\N	SSH connection failed: Failed to establish SSH connection
5	00e840c6-ebfb-4214-8b37-1de631c6da55	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-08-27 13:50:36.241817	2025-08-27 13:51:01.059633	completed	2	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 52 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
6	0d23c55d-8939-4cb2-8c76-262a28589f23	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-08-27 14:20:19.311034	2025-08-27 14:20:41.708347	completed	2	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 52 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
7	4e0aab63-222d-4e98-a417-bf1b8d174a32	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-08-28 12:48:23.999412	2025-08-28 12:48:45.428977	completed	4	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 51 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
8	4fb4b759-3824-4650-84ee-f6ebd1315e66	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-08-28 12:55:39.113623	2025-08-28 12:56:01.289012	completed	4	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 51 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
9	404894c6-2ab7-4ac2-892a-777c1f452f1f	1	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-07 13:09:00.966359	\N	running	5	\N	\N	f	f	\N	\N	\N	\N
10	bd02f358-08d0-4656-8c98-b8e428c21d77	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-07 13:10:09.777233	\N	running	5	\N	\N	f	f	\N	\N	\N	\N
11	62a4fa01-3ae6-4dc9-a3d6-ee4cab9d18ee	1	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-07 14:07:11.252973	2025-09-07 14:07:37.144831	completed	5	\N	\N	f	f	\N	\N	🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🖥️  No domain found. Falling back to IP: 78.46.216.107\n⏳ Waiting for .NET backend to become ready at http://78.46.216.107/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
12	e6d6b733-02d5-4bd6-8821-9a24790f3427	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-07 14:08:10.696988	\N	running	5	\N	\N	f	f	\N	\N	\N	\N
13	7c37a8a2-c00a-4599-8a38-16f9fe1e161b	1	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-07 14:08:52.822785	2025-09-07 14:09:05.247213	completed	5	\N	\N	f	f	\N	\N	🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🖥️  No domain found. Falling back to IP: 78.46.216.107\n⏳ Waiting for .NET backend to become ready at http://78.46.216.107/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
14	977d1307-2238-4cba-b626-962bc8a0f9e6	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-08 10:29:36.730145	\N	running	5	\N	\N	f	f	\N	\N	\N	\N
15	29381d78-eafd-48c5-a5b4-02f1cf891164	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-08 22:42:39.751033	2025-09-08 22:43:02.574585	completed	1	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
16	48a6b0f7-c4a8-4ac4-8546-b31b394432b8	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 11:03:16.345653	2025-09-09 11:03:39.232777	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
17	bce5c200-253d-4d92-9f37-31a90abf64ee	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 11:08:10.042672	2025-09-09 11:08:32.302648	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
18	65b1b39c-aea9-4fbd-a1d7-4c8b3bded933	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 11:14:00.102435	2025-09-09 11:14:22.827477	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
19	36e2801d-6511-429e-b126-bc3365285053	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 11:20:21.362135	2025-09-09 11:20:43.138986	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
20	0b7fe80f-7f66-4074-aa37-937ac36426d0	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 11:26:29.201904	2025-09-09 11:26:51.043586	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
21	f2847b02-5c68-46a0-80c2-428a5634e6ff	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 11:27:30.881691	2025-09-09 11:27:52.435749	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
22	f94082f7-9bee-4f96-ab9d-193eef98720c	6	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 12:01:32.651169	\N	running	5	\N	\N	f	f	\N	\N	\N	\N
23	4656b470-db4b-4cc6-9b44-5055baab321c	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 12:04:41.935393	2025-09-09 12:05:04.057756	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
24	1bb1c653-68f5-4693-a55f-ad5793c0a38c	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 12:12:46.001033	2025-09-09 12:13:08.513925	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
25	fc90388a-79be-44ed-b65d-fd6528e4a9df	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 13:21:06.914835	2025-09-09 13:21:27.654812	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
26	03ef3604-fe01-4a70-8141-0899426ab045	9	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-09 13:24:57.458492	2025-09-09 13:25:19.824716	completed	5	\N	\N	f	f	\N	\N	🌐 Checking certificate status for: test.novahrs.com\n🔄 Certificate already exists. Attempting renewal for test.novahrs.com...\n✅ Certificate renewal attempted (certbot decides if renewal is necessary).\n\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\nFound the following certs:\n  Certificate Name: test.novahrs.com\n    Serial Number: 6330579043378a831d769e8f8d30b56fbd7\n    Key Type: ECDSA\n    Domains: test.novahrs.com\n    Expiry Date: 2025-10-18 18:26:09+00:00 (VALID: 39 days)\n    Certificate Path: /etc/letsencrypt/live/test.novahrs.com/fullchain.pem\n    Private Key Path: /etc/letsencrypt/live/test.novahrs.com/privkey.pem\n- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -\n🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🌐 Domain detected: test.novahrs.com\n⏳ Waiting for .NET backend to become ready at https://test.novahrs.com/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n🔁 Still waiting... (10)\n🔁 Still waiting... (11)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n[]	\N
27	4ea70637-4514-4fa0-a122-a4bca4dd9b4f	52	deployment	Nova HR Docker deployment script execution	\N	f	f	f	\N	2025-09-11 17:06:14.517801	2025-09-11 17:06:28.958733	completed	5	\N	\N	f	f	\N	\N	🔄 Pulling latest images...\n🛑 Shutting down old containers...\n🚀 Starting services...\n🖥️  No domain found. Falling back to IP: 158.220.94.206\n⏳ Waiting for .NET backend to become ready at http://158.220.94.206/dotnet/excecutescript\n🔁 Still waiting... (1)\n🔁 Still waiting... (2)\n🔁 Still waiting... (3)\n🔁 Still waiting... (4)\n🔁 Still waiting... (5)\n🔁 Still waiting... (6)\n🔁 Still waiting... (7)\n🔁 Still waiting... (8)\n🔁 Still waiting... (9)\n✅ .NET backend is ready\n📡 Calling executescript endpoint...\n	\N
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."user" (id, username, email, password_hash, role, active, created_at, is_manager, is_approved, profile_image) FROM stdin;
2	tech_agent	tech@company.com	scrypt:32768:8:1$RljMQwDgQQKW83v9$2944019dbe83456df8ff9a17a6f0ca8afde536d2d19627119b6fd2ecd20279b1df2271aa6c97634747360f372286c086ec0aeb00f51b8dd3dbf2ddcf2bd14a6b	TECHNICAL_AGENT	t	2025-08-27 11:10:22.456549	f	t	\N
3	sales_agent	sales@company.com	scrypt:32768:8:1$BahnUduXmpPhALBQ$36f47b2dabd54d9472fc2d3572839eedb286bf3d51d840103442a1d7fbe0ff626c962d0249562ab78965fe54130898c3db7114e88ceb3447f40a3d8311599646	SALES_AGENT	t	2025-08-27 11:10:23.319879	f	t	\N
6	m.hassan	m.hassan@test.com	scrypt:32768:8:1$y38PHuVBPRXo0lkl$feb0014c141d6f86054d77301b9e3898883857ef2606532e4a43e8551038669b1203370e4c0eddbb59899f55b463f08578a2564224e5e52c5e9f38a7309f718d	ADMIN	t	2025-08-28 11:45:14.34718	f	t	\N
8	othman	othman@dynamiceg.com	scrypt:32768:8:1$yUBoxMQcXnQLNYNV$25007a72e693e616686865c0a29ee34e8719e7b464f534deeb6d9fb1281dd1a12a05955131f4ed3252820c055033314d48596b1239c529a8ef9931406386d21c	SALES_AGENT	t	2025-09-02 18:52:39.772242	f	t	\N
1	admin	admin@company.com	scrypt:32768:8:1$PRAf5fo8HVJIzOH9$c30c6153a34c1f63c09a565fc9ce3bcff5121cdbd2e21fa06d92b2b611629acddecf272901db97933d3c1fb6ab228ff57060fbab6b840ed858ea43f9ca001381	ADMIN	t	2025-08-27 11:10:21.617969	f	t	\N
5	tokhy	tokhy@company.com	scrypt:32768:8:1$hF2qX3JPPamJEJdu$16cfe5b0bc6e8b63f0930bdd807b8de6ef2732689e6b71336f2f39c7226fba8571946c73116048ff0109d5ca2687e419a976d2ca7c9a399cf84ef2328023e8b4	TECHNICAL_AGENT	t	2025-08-27 14:52:42.673393	t	t	\N
4	sohila	sohila@company.com	scrypt:32768:8:1$7w3YFkba4bNNFRzt$87e078b44b3209b4fb5e1142ee08ac23a94541ef4c955d301c085654733e0fabf8fb8a441c2123fe13a2ab5a5f60ff12383e462de80482d3b29ea244288391f3	TECHNICAL_AGENT	t	2025-08-27 14:35:17.761148	f	t	\N
\.


--
-- Data for Name: user_project_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_project_access (id, user_id, project_id, access_level, granted_at, granted_by) FROM stdin;
1	2	1	write	2025-08-27 14:19:30.686526	1
2	2	2	read	2025-08-27 14:19:30.982153	1
3	3	1	read	2025-08-27 14:19:31.269197	1
7	4	1	write	2025-08-27 14:36:55.175838	1
14	5	1	admin	2025-09-08 11:16:38.19889	1
\.


--
-- Data for Name: user_server_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_server_access (id, user_id, server_id, access_level, assigned_at, assigned_by) FROM stdin;
2	4	3	write	2025-08-28 12:10:37.208358	1
3	4	7	write	2025-08-28 12:11:01.632514	1
4	4	14	write	2025-08-28 12:11:25.191596	1
6	4	5	write	2025-08-28 12:41:27.662547	5
8	4	6	write	2025-08-28 12:42:02.969841	5
9	4	9	write	2025-08-28 12:43:25.985758	5
12	4	1	write	\N	1
1	4	2	read	2025-08-28 12:10:09.175448	1
14	4	52	write	2025-09-11 17:12:31.175699	5
\.


--
-- Name: client_subscription_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.client_subscription_id_seq', 1, false);


--
-- Name: database_backup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.database_backup_id_seq', 39, true);


--
-- Name: deployment_execution_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.deployment_execution_id_seq', 1, false);


--
-- Name: deployment_script_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.deployment_script_id_seq', 1, false);


--
-- Name: hetzner_projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.hetzner_projects_id_seq', 3, true);


--
-- Name: hetzner_server_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.hetzner_server_id_seq', 52, true);


--
-- Name: notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notification_id_seq', 2, true);


--
-- Name: server_request_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.server_request_id_seq', 2, true);


--
-- Name: system_update_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.system_update_id_seq', 27, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_id_seq', 8, true);


--
-- Name: user_project_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_project_access_id_seq', 14, true);


--
-- Name: user_server_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_server_access_id_seq', 14, true);


--
-- Name: client_subscription client_subscription_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_subscription
    ADD CONSTRAINT client_subscription_pkey PRIMARY KEY (id);


--
-- Name: database_backup database_backup_backup_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_backup
    ADD CONSTRAINT database_backup_backup_id_key UNIQUE (backup_id);


--
-- Name: database_backup database_backup_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_backup
    ADD CONSTRAINT database_backup_pkey PRIMARY KEY (id);


--
-- Name: deployment_execution deployment_execution_execution_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_execution
    ADD CONSTRAINT deployment_execution_execution_id_key UNIQUE (execution_id);


--
-- Name: deployment_execution deployment_execution_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_execution
    ADD CONSTRAINT deployment_execution_pkey PRIMARY KEY (id);


--
-- Name: deployment_script deployment_script_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_script
    ADD CONSTRAINT deployment_script_pkey PRIMARY KEY (id);


--
-- Name: hetzner_projects hetzner_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_projects
    ADD CONSTRAINT hetzner_projects_pkey PRIMARY KEY (id);


--
-- Name: hetzner_projects hetzner_projects_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_projects
    ADD CONSTRAINT hetzner_projects_project_id_key UNIQUE (project_id);


--
-- Name: hetzner_server hetzner_server_hetzner_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_server
    ADD CONSTRAINT hetzner_server_hetzner_id_key UNIQUE (hetzner_id);


--
-- Name: hetzner_server hetzner_server_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_server
    ADD CONSTRAINT hetzner_server_pkey PRIMARY KEY (id);


--
-- Name: notification notification_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_pkey PRIMARY KEY (id);


--
-- Name: server_request server_request_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.server_request
    ADD CONSTRAINT server_request_pkey PRIMARY KEY (id);


--
-- Name: server_request server_request_request_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.server_request
    ADD CONSTRAINT server_request_request_id_key UNIQUE (request_id);


--
-- Name: system_update system_update_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_update
    ADD CONSTRAINT system_update_pkey PRIMARY KEY (id);


--
-- Name: system_update system_update_update_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_update
    ADD CONSTRAINT system_update_update_id_key UNIQUE (update_id);


--
-- Name: user_server_access unique_user_server; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_server_access
    ADD CONSTRAINT unique_user_server UNIQUE (user_id, server_id);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user_project_access user_project_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_project_access
    ADD CONSTRAINT user_project_access_pkey PRIMARY KEY (id);


--
-- Name: user_project_access user_project_access_user_id_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_project_access
    ADD CONSTRAINT user_project_access_user_id_project_id_key UNIQUE (user_id, project_id);


--
-- Name: user_server_access user_server_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_server_access
    ADD CONSTRAINT user_server_access_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: idx_hetzner_server_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hetzner_server_project_id ON public.hetzner_server USING btree (project_id);


--
-- Name: client_subscription client_subscription_managed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_subscription
    ADD CONSTRAINT client_subscription_managed_by_fkey FOREIGN KEY (managed_by) REFERENCES public."user"(id);


--
-- Name: client_subscription client_subscription_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_subscription
    ADD CONSTRAINT client_subscription_server_id_fkey FOREIGN KEY (server_id) REFERENCES public.hetzner_server(id);


--
-- Name: database_backup database_backup_initiated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_backup
    ADD CONSTRAINT database_backup_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES public."user"(id);


--
-- Name: database_backup database_backup_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.database_backup
    ADD CONSTRAINT database_backup_server_id_fkey FOREIGN KEY (server_id) REFERENCES public.hetzner_server(id);


--
-- Name: deployment_execution deployment_execution_executed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_execution
    ADD CONSTRAINT deployment_execution_executed_by_fkey FOREIGN KEY (executed_by) REFERENCES public."user"(id);


--
-- Name: deployment_execution deployment_execution_script_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_execution
    ADD CONSTRAINT deployment_execution_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.deployment_script(id);


--
-- Name: deployment_execution deployment_execution_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_execution
    ADD CONSTRAINT deployment_execution_server_id_fkey FOREIGN KEY (server_id) REFERENCES public.hetzner_server(id);


--
-- Name: deployment_script deployment_script_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deployment_script
    ADD CONSTRAINT deployment_script_created_by_fkey FOREIGN KEY (created_by) REFERENCES public."user"(id);


--
-- Name: hetzner_projects hetzner_projects_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_projects
    ADD CONSTRAINT hetzner_projects_created_by_fkey FOREIGN KEY (created_by) REFERENCES public."user"(id);


--
-- Name: hetzner_server hetzner_server_managed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_server
    ADD CONSTRAINT hetzner_server_managed_by_fkey FOREIGN KEY (managed_by) REFERENCES public."user"(id);


--
-- Name: hetzner_server hetzner_server_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hetzner_server
    ADD CONSTRAINT hetzner_server_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.hetzner_projects(id);


--
-- Name: notification notification_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_request_id_fkey FOREIGN KEY (request_id) REFERENCES public.server_request(id);


--
-- Name: notification notification_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notification
    ADD CONSTRAINT notification_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: server_request server_request_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.server_request
    ADD CONSTRAINT server_request_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.hetzner_projects(id);


--
-- Name: server_request server_request_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.server_request
    ADD CONSTRAINT server_request_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public."user"(id);


--
-- Name: server_request server_request_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.server_request
    ADD CONSTRAINT server_request_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: system_update system_update_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_update
    ADD CONSTRAINT system_update_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public."user"(id);


--
-- Name: system_update system_update_initiated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_update
    ADD CONSTRAINT system_update_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES public."user"(id);


--
-- Name: system_update system_update_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.system_update
    ADD CONSTRAINT system_update_server_id_fkey FOREIGN KEY (server_id) REFERENCES public.hetzner_server(id);


--
-- Name: user_project_access user_project_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_project_access
    ADD CONSTRAINT user_project_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES public."user"(id);


--
-- Name: user_project_access user_project_access_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_project_access
    ADD CONSTRAINT user_project_access_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.hetzner_projects(id) ON DELETE CASCADE;


--
-- Name: user_project_access user_project_access_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_project_access
    ADD CONSTRAINT user_project_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: user_server_access user_server_access_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_server_access
    ADD CONSTRAINT user_server_access_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public."user"(id);


--
-- Name: user_server_access user_server_access_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_server_access
    ADD CONSTRAINT user_server_access_server_id_fkey FOREIGN KEY (server_id) REFERENCES public.hetzner_server(id);


--
-- Name: user_server_access user_server_access_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_server_access
    ADD CONSTRAINT user_server_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- PostgreSQL database dump complete
--

