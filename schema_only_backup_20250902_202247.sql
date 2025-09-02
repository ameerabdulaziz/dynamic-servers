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
    project_id integer,
    reverse_dns character varying(255)
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

