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
    ssh_last_test timestamp without time zone
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
    hetzner_id integer NOT NULL,
    name character varying(100) NOT NULL,
    status character varying(20) NOT NULL,
    server_type character varying(50) NOT NULL,
    image character varying(100) NOT NULL,
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
    project_id integer
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
    application_name character varying(100) NOT NULL,
    application_type character varying(50) NOT NULL,
    application_description text,
    business_justification text NOT NULL,
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
    deployment_progress integer
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
    is_approved boolean DEFAULT true
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

COPY public.hetzner_projects (id, project_id, name, description, hetzner_api_token, is_active, created_at, updated_at, created_by, max_servers, monthly_budget, ssh_username, ssh_port, ssh_private_key, ssh_public_key, ssh_key_passphrase, ssh_connection_tested, ssh_last_test) FROM stdin;
2	PRJB04B92B7	Frappe ERP	Enterprise Resource Planning system with CRM, accounting, inventory, and project management modules	USE_ENV_TOKEN	t	2025-08-27 11:28:54.264775	2025-08-27 11:28:54.264779	1	15	500.00	root	22	\N	\N	\N	f	\N
3	PRJCFB5FA17	Django Projects	Development and staging environment for Django-based web applications and API services	USE_ENV_TOKEN	f	2025-08-27 11:28:54.552061	2025-08-27 11:28:54.552066	1	15	500.00	root	22	\N	\N	\N	f	\N
1	PRJAAAE7800	Nova HR	Human Resources management platform with employee onboarding, payroll, and performance tracking systems	XI2WWI08YXZYgZzIAWKs7C7cN5Q3vscmP5tnEsjoof5Vg6XXsAhKgKExGvk3cnNk	t	2025-08-27 11:28:53.962701	2025-08-27 13:48:35.854941	1	15	500.00	dynamic	22	-----BEGIN OPENSSH PRIVATE KEY-----\r\nb3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW\r\nQyNTUxOQAAACDLh6oftMV8xx/PQ3iKmMyMpXG/dKQTAxnQT8DvLMDxbwAAAJgkkdOaJJHT\r\nmgAAAAtzc2gtZWQyNTUxOQAAACDLh6oftMV8xx/PQ3iKmMyMpXG/dKQTAxnQT8DvLMDxbw\r\nAAAECkzw8GvkjVQgJsHrKlQMmJoVxFyaroBfvgD5gGSDTQHsuHqh+0xXzHH89DeIqYzIyl\r\ncb90pBMDGdBPwO8swPFvAAAAFGFtZWVyQHByZWNpc2lvbi03NzIwAQ==\r\n-----END OPENSSH PRIVATE KEY-----	ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMuHqh+0xXzHH89DeIqYzIylcb90pBMDGdBPwO8swPFv ameer@precision-7720		t	2025-08-27 13:48:35.853587
\.


--
-- Data for Name: hetzner_server; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.hetzner_server (id, hetzner_id, name, status, server_type, image, public_ip, private_ip, ipv6, datacenter, location, cpu_cores, memory_gb, disk_gb, created_at, last_synced, managed_by, deployment_status, deployment_log, last_deployment, project_id) FROM stdin;
2	62483982	ehaf	running	cpx21	docker-ce	91.99.54.0	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-08-27 12:08:44.370255	2025-08-27 12:08:44.369241	\N	none	\N	\N	1
3	62731319	world-aviation	running	cpx21	docker-ce	91.99.73.182	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-08-27 12:08:44.660892	2025-08-27 12:08:44.659312	\N	none	\N	\N	1
4	62880147	delta-el-nile	running	cx32	docker-ce	138.199.194.67	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:44.948799	2025-08-27 12:08:44.947702	\N	none	\N	\N	1
1	62483369	sabahy	running	cpx21	docker-ce	78.46.216.107	\N	\N	nbg1-dc3	nbg1	3	4	80	2025-08-27 12:08:44.068947	2025-08-27 12:08:44.066796	\N	none	\N	\N	1
5	62880148	ecip	running	cx32	docker-ce	167.235.136.56	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:45.256048	2025-08-27 12:08:45.2551	\N	none	\N	\N	1
6	63231869	inspire	running	cx32	docker-ce	91.99.20.203	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:45.547047	2025-08-27 12:08:45.546322	\N	none	\N	\N	1
7	63231871	mokambo	running	cx32	docker-ce	162.55.62.13	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:45.835313	2025-08-27 12:08:45.834329	\N	none	\N	\N	1
8	63894842	petronas	running	cx32	docker-ce	138.199.221.171	\N	\N	nbg1-dc3	nbg1	4	8	80	2025-08-27 12:08:46.132898	2025-08-27 12:08:46.131835	\N	none	\N	\N	1
10	64918700	nova-hr-mail	running	cx32	docker-ce	157.180.95.159	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:46.710622	2025-08-27 12:08:46.70938	\N	none	\N	\N	1
11	100739667	technosat	running	cx32	docker-ce	95.216.219.177	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.005951	2025-08-27 12:08:47.005242	\N	none	\N	\N	1
12	103163473	spc	running	cx32	docker-ce	65.108.213.57	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.295771	2025-08-27 12:08:47.295017	\N	none	\N	\N	1
13	103190743	dynamic	running	cx32	docker-ce	46.62.129.242	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.584269	2025-08-27 12:08:47.583329	\N	none	\N	\N	1
14	103890656	hamam-abdo	running	cx32	docker-ce	157.180.84.86	\N	\N	hel1-dc2	hel1	4	8	80	2025-08-27 12:08:47.872042	2025-08-27 12:08:47.871056	\N	none	\N	\N	1
15	105385555	rtx	running	cx22	docker-ce	95.216.138.122	\N	\N	hel1-dc2	hel1	2	4	40	2025-08-27 12:08:48.164152	2025-08-27 12:08:48.16297	\N	none	\N	\N	1
9	64052824	nova-hr-test	running	cx32	docker-ce	168.119.249.64	\N	\N	fsn1-dc14	fsn1	4	8	80	2025-08-27 12:08:46.421082	2025-08-27 12:08:46.420351	\N	none	\N	\N	1
\.


--
-- Data for Name: notification; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notification (id, user_id, title, message, type, is_read, created_at, request_id) FROM stdin;
\.


--
-- Data for Name: server_request; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.server_request (id, request_id, user_id, server_name, server_type, cpu_cores, memory_gb, storage_gb, operating_system, application_name, application_type, application_description, business_justification, estimated_usage, status, priority, created_at, reviewed_at, deployed_at, reviewed_by, admin_notes, deployment_notes, server_ip, deployment_progress) FROM stdin;
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
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public."user" (id, username, email, password_hash, role, active, created_at, is_manager, is_approved) FROM stdin;
2	tech_agent	tech@company.com	scrypt:32768:8:1$HU1IdM3I8BkA7US4$a8f523c83c9cdf5cc33e38d466ccf0978565914608956ceafbb89a56a41120aaabb55613922d3fedd1f4b8ee6e226072fa345c5cbe52d025e7362b2b649375d8	TECHNICAL_AGENT	t	2025-08-27 11:10:22.456549	f	t
3	sales_agent	sales@company.com	scrypt:32768:8:1$7RVkGyZZ0FpafzWJ$de68a8845a6b918b1c40fc4366549e518780b40c6b98f682420dc3968be7fdb7420ba6f088229e16346b06a30b7a9ce87f7cd1330a340f3d0f40d1bcb04df51d	SALES_AGENT	t	2025-08-27 11:10:23.319879	f	t
6	m.hassan	m.hassan@test.com	scrypt:32768:8:1$dD6Q6jYysQqa8Oae$b64fe38623dd769f3742a553d0af7cd794fccec9e1ff82b691387c9adcfd48230299c149b0339c9ff3ccd31d97578c08c1f92730f8230119cb8b84ea4f07a97c	SALES_AGENT	t	2025-08-28 11:45:14.34718	f	t
1	admin	admin@company.com	scrypt:32768:8:1$tHsVn7ekGduCzpg5$59daba98dea61bfdf1ccab1760095eb42fd064c376611329859c7d68be1b2331cf56bcbfdeb6110805822df7b7e4c7dcf0e413b16949d1afd00368bc776282ec	ADMIN	t	2025-08-27 11:10:21.617969	f	t
4	sohila	sohila@company.com	scrypt:32768:8:1$MwtLbgt7rOtSweqf$2b6bea3414c06864969946a883174061c019780ab24dde41468ad718bfe39ffccb602136ad7845606b68897c66d9662fc2f9cca3087d625392306c80ca8b2208	TECHNICAL_AGENT	t	2025-08-27 14:35:17.761148	f	t
5	tokhy	tokhy@company.com	scrypt:32768:8:1$J2A2W5ljDVoC3h8s$7ef4ee2449e343673d6583245bbc776de25e6e98f2dd7ba5e2e606e6e5748b69960b94378b905e39cba3b8b9cae823d14deb72b427e719db5cb5a9a634b5c5be	TECHNICAL_AGENT	t	2025-08-27 14:52:42.673393	t	t
7	youssef	youssef@test.com	scrypt:32768:8:1$pbX6Vbm6dcVLjsWy$4afed92ce9d4cc03de75a1b6c6decf7816a4ade9e3ac1ec748efa4070be903e9138dfbaf982895fca7e842c75b70edd1e5e38979983f021a1a1017d575f391f1	TECHNICAL_AGENT	t	2025-08-28 11:54:57.284674	f	t
\.


--
-- Data for Name: user_project_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_project_access (id, user_id, project_id, access_level, granted_at, granted_by) FROM stdin;
1	2	1	write	2025-08-27 14:19:30.686526	1
2	2	2	read	2025-08-27 14:19:30.982153	1
3	3	1	read	2025-08-27 14:19:31.269197	1
7	4	1	write	2025-08-27 14:36:55.175838	1
8	5	1	admin	2025-08-27 14:52:53.415309	1
\.


--
-- Data for Name: user_server_access; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_server_access (id, user_id, server_id, access_level, assigned_at, assigned_by) FROM stdin;
1	4	2	write	2025-08-28 12:10:09.175448	1
2	4	3	write	2025-08-28 12:10:37.208358	1
3	4	7	write	2025-08-28 12:11:01.632514	1
4	4	14	write	2025-08-28 12:11:25.191596	1
5	7	4	write	2025-08-28 12:41:07.716016	5
6	4	5	write	2025-08-28 12:41:27.662547	5
7	7	1	write	2025-08-28 12:41:42.936338	5
8	4	6	write	2025-08-28 12:42:02.969841	5
9	4	9	write	2025-08-28 12:43:25.985758	5
\.


--
-- Name: client_subscription_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.client_subscription_id_seq', 1, false);


--
-- Name: database_backup_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.database_backup_id_seq', 19, true);


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

SELECT pg_catalog.setval('public.hetzner_server_id_seq', 21, true);


--
-- Name: notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.notification_id_seq', 1, false);


--
-- Name: server_request_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.server_request_id_seq', 1, false);


--
-- Name: system_update_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.system_update_id_seq', 8, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_id_seq', 7, true);


--
-- Name: user_project_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_project_access_id_seq', 8, true);


--
-- Name: user_server_access_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.user_server_access_id_seq', 9, true);


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

