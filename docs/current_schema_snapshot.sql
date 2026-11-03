--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
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
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_conversations (
    conversation_id bigint NOT NULL,
    user_id bigint NOT NULL,
    title character varying(200),
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_message_at timestamp with time zone,
    ended_at timestamp with time zone,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT chk_ai_conversation_status CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'closed'::character varying, 'archived'::character varying])::text[])))
);


--
-- Name: ai_conversations_conversation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.ai_conversations ALTER COLUMN conversation_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ai_conversations_conversation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ai_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_messages (
    message_id bigint NOT NULL,
    conversation_id bigint NOT NULL,
    sender_type character varying(20) NOT NULL,
    content text NOT NULL,
    model_name character varying(100),
    token_count integer,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_ai_message_sender CHECK (((sender_type)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying, 'system'::character varying, 'tool'::character varying])::text[]))),
    CONSTRAINT chk_ai_message_token_count CHECK (((token_count IS NULL) OR (token_count >= 0)))
);


--
-- Name: ai_messages_message_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.ai_messages ALTER COLUMN message_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ai_messages_message_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ai_tool_executions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_tool_executions (
    tool_execution_id bigint NOT NULL,
    conversation_id bigint NOT NULL,
    message_id bigint,
    user_id bigint,
    tool_name character varying(100) NOT NULL,
    input_arguments jsonb DEFAULT '{}'::jsonb NOT NULL,
    execution_status character varying(20) DEFAULT 'started'::character varying NOT NULL,
    result_summary text,
    error_code character varying(100),
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at timestamp with time zone,
    CONSTRAINT chk_ai_tool_execution_status CHECK (((execution_status)::text = ANY ((ARRAY['started'::character varying, 'succeeded'::character varying, 'failed'::character varying, 'denied'::character varying])::text[]))),
    CONSTRAINT chk_ai_tool_execution_times CHECK (((completed_at IS NULL) OR (completed_at >= started_at)))
);


--
-- Name: ai_tool_executions_tool_execution_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.ai_tool_executions ALTER COLUMN tool_execution_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ai_tool_executions_tool_execution_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    audit_log_id bigint NOT NULL,
    actor_user_id bigint,
    action character varying(100) NOT NULL,
    entity_type character varying(100),
    entity_id character varying(100),
    details jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: audit_logs_audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.audit_logs ALTER COLUMN audit_log_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.audit_logs_audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: departments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.departments (
    department_id bigint NOT NULL,
    department_name character varying(100) NOT NULL,
    department_code character varying(30),
    parent_department_id bigint,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: departments_department_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.departments ALTER COLUMN department_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.departments_department_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: employee_code_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.employee_code_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    employee_id bigint NOT NULL,
    employee_code character varying(20) DEFAULT ('EMP'::text || lpad((nextval('public.employee_code_seq'::regclass))::text, 3, '0'::text)) NOT NULL,
    full_name character varying(150) NOT NULL,
    email character varying(255) NOT NULL,
    department character varying(100),
    job_title character varying(100),
    hire_date date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    department_id bigint,
    manager_employee_id bigint
);


--
-- Name: employees_employee_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.employees ALTER COLUMN employee_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.employees_employee_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: hr_document_request_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hr_document_request_history (
    history_id bigint NOT NULL,
    document_request_id bigint NOT NULL,
    previous_status character varying(20),
    new_status character varying(20) NOT NULL,
    action_by_user_id bigint,
    comments text,
    action_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_document_history_new_status CHECK (((new_status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'rejected'::character varying, 'cancelled'::character varying])::text[]))),
    CONSTRAINT chk_document_history_previous_status CHECK (((previous_status IS NULL) OR ((previous_status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'rejected'::character varying, 'cancelled'::character varying])::text[]))))
);


--
-- Name: hr_document_request_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.hr_document_request_history ALTER COLUMN history_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.hr_document_request_history_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: hr_document_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hr_document_requests (
    document_request_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    document_type character varying(50) NOT NULL,
    purpose text,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    requested_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    processed_by_employee_id bigint,
    processed_at timestamp with time zone,
    remarks text,
    document_reference character varying(255),
    CONSTRAINT chk_document_request_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'rejected'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: hr_document_requests_document_request_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.hr_document_requests ALTER COLUMN document_request_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.hr_document_requests_document_request_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: hr_document_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hr_document_types (
    document_type_id bigint NOT NULL,
    document_type_code character varying(50) NOT NULL,
    document_type_name character varying(120) NOT NULL,
    description text,
    requires_hr_approval boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: hr_document_types_document_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.hr_document_types ALTER COLUMN document_type_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.hr_document_types_document_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: hr_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hr_policies (
    policy_id bigint NOT NULL,
    policy_code character varying(50) NOT NULL,
    policy_title character varying(250) NOT NULL,
    policy_category character varying(100) NOT NULL,
    description text,
    department_id bigint,
    owner_user_id bigint,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_hr_policies_category_not_blank CHECK ((btrim((policy_category)::text) <> ''::text)),
    CONSTRAINT chk_hr_policies_code_not_blank CHECK ((btrim((policy_code)::text) <> ''::text)),
    CONSTRAINT chk_hr_policies_status CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'pending_review'::character varying, 'approved'::character varying, 'published'::character varying, 'archived'::character varying, 'rejected'::character varying])::text[]))),
    CONSTRAINT chk_hr_policies_title_not_blank CHECK ((btrim((policy_title)::text) <> ''::text))
);


--
-- Name: hr_policies_policy_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.hr_policies ALTER COLUMN policy_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.hr_policies_policy_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: hr_policy_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hr_policy_chunks (
    policy_chunk_id bigint NOT NULL,
    policy_version_id bigint NOT NULL,
    chunk_number integer NOT NULL,
    section_heading character varying(500),
    chunk_text text NOT NULL,
    page_number integer,
    source_reference text,
    embedding_model character varying(100) DEFAULT 'gemini-embedding-001'::character varying NOT NULL,
    embedding_dimensions smallint DEFAULT 3072 NOT NULL,
    embedding public.halfvec(3072),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, (((COALESCE(section_heading, ''::character varying))::text || ' '::text) || chunk_text))) STORED,
    CONSTRAINT chk_hr_policy_chunk_number CHECK ((chunk_number > 0)),
    CONSTRAINT chk_hr_policy_chunk_text CHECK ((btrim(chunk_text) <> ''::text)),
    CONSTRAINT chk_hr_policy_embedding_dimensions CHECK ((embedding_dimensions = 3072)),
    CONSTRAINT chk_hr_policy_embedding_model CHECK (((embedding_model)::text = 'gemini-embedding-001'::text)),
    CONSTRAINT chk_hr_policy_page_number CHECK (((page_number IS NULL) OR (page_number > 0)))
);


--
-- Name: hr_policy_chunks_policy_chunk_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.hr_policy_chunks ALTER COLUMN policy_chunk_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.hr_policy_chunks_policy_chunk_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: hr_policy_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hr_policy_versions (
    policy_version_id bigint NOT NULL,
    policy_id bigint NOT NULL,
    version_number integer NOT NULL,
    version_label character varying(50),
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    effective_from date,
    effective_to date,
    submitted_at timestamp with time zone,
    approved_by_user_id bigint,
    approved_at timestamp with time zone,
    published_at timestamp with time zone,
    source_file_name character varying(500),
    source_reference text,
    change_summary text,
    created_by_user_id bigint,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_hr_policy_approval_metadata CHECK ((((approved_at IS NULL) AND (approved_by_user_id IS NULL)) OR ((approved_at IS NOT NULL) AND (approved_by_user_id IS NOT NULL)))),
    CONSTRAINT chk_hr_policy_effective_dates CHECK (((effective_to IS NULL) OR (effective_from IS NULL) OR (effective_to >= effective_from))),
    CONSTRAINT chk_hr_policy_published_metadata CHECK ((((status)::text <> 'published'::text) OR (published_at IS NOT NULL))),
    CONSTRAINT chk_hr_policy_version_positive CHECK ((version_number > 0)),
    CONSTRAINT chk_hr_policy_version_status CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'pending_review'::character varying, 'approved'::character varying, 'published'::character varying, 'archived'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Name: hr_policy_versions_policy_version_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.hr_policy_versions ALTER COLUMN policy_version_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.hr_policy_versions_policy_version_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: leave_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leave_approvals (
    leave_approval_id bigint NOT NULL,
    leave_request_id bigint NOT NULL,
    approver_employee_id bigint NOT NULL,
    decision character varying(20) NOT NULL,
    comments text,
    decided_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_leave_approval_decision CHECK (((decision)::text = ANY ((ARRAY['approved'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Name: leave_approvals_leave_approval_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.leave_approvals ALTER COLUMN leave_approval_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.leave_approvals_leave_approval_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: leave_balances; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leave_balances (
    leave_balance_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    leave_type character varying(30) NOT NULL,
    entitlement_days numeric(6,2) DEFAULT 0 NOT NULL,
    used_days numeric(6,2) DEFAULT 0 NOT NULL,
    balance_year integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_entitlement_days CHECK ((entitlement_days >= (0)::numeric)),
    CONSTRAINT chk_used_days CHECK (((used_days >= (0)::numeric) AND (used_days <= entitlement_days)))
);


--
-- Name: leave_balances_leave_balance_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.leave_balances ALTER COLUMN leave_balance_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.leave_balances_leave_balance_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: leave_entitlement_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leave_entitlement_rules (
    entitlement_rule_id bigint NOT NULL,
    leave_type_id bigint NOT NULL,
    employment_category character varying(50) DEFAULT 'all'::character varying NOT NULL,
    entitlement_days numeric(7,2) NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_entitlement_rule_dates CHECK (((effective_to IS NULL) OR (effective_to >= effective_from))),
    CONSTRAINT chk_entitlement_rule_days CHECK ((entitlement_days >= (0)::numeric))
);


--
-- Name: leave_entitlement_rules_entitlement_rule_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.leave_entitlement_rules ALTER COLUMN entitlement_rule_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.leave_entitlement_rules_entitlement_rule_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: leave_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leave_requests (
    leave_request_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    leave_type character varying(30) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    days_requested numeric(6,2) NOT NULL,
    reason text,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    submitted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_days_requested CHECK ((days_requested > (0)::numeric)),
    CONSTRAINT chk_leave_dates CHECK ((end_date >= start_date)),
    CONSTRAINT chk_leave_request_status CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying, 'cancelled'::character varying])::text[])))
);


--
-- Name: leave_requests_leave_request_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.leave_requests ALTER COLUMN leave_request_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.leave_requests_leave_request_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: leave_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leave_transactions (
    leave_transaction_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    leave_balance_id bigint NOT NULL,
    leave_request_id bigint,
    transaction_type character varying(20) NOT NULL,
    days_delta numeric(7,2) NOT NULL,
    notes text,
    actor_user_id bigint,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_leave_transaction_nonzero CHECK ((days_delta <> (0)::numeric)),
    CONSTRAINT chk_leave_transaction_sign CHECK ((((transaction_type)::text <> ALL ((ARRAY['accrual'::character varying, 'usage'::character varying])::text[])) OR (((transaction_type)::text = 'accrual'::text) AND (days_delta > (0)::numeric)) OR (((transaction_type)::text = 'usage'::text) AND (days_delta < (0)::numeric)))),
    CONSTRAINT chk_leave_transaction_type CHECK (((transaction_type)::text = ANY ((ARRAY['accrual'::character varying, 'usage'::character varying, 'adjustment'::character varying, 'reversal'::character varying])::text[])))
);


--
-- Name: leave_transactions_leave_transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.leave_transactions ALTER COLUMN leave_transaction_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.leave_transactions_leave_transaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: leave_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.leave_types (
    leave_type_id bigint NOT NULL,
    leave_type_code character varying(30) NOT NULL,
    leave_type_name character varying(100) NOT NULL,
    description text,
    is_paid boolean DEFAULT true NOT NULL,
    requires_approval boolean DEFAULT true NOT NULL,
    min_notice_calendar_days integer DEFAULT 0 NOT NULL,
    max_consecutive_days numeric(6,2),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_leave_type_max_days CHECK (((max_consecutive_days IS NULL) OR (max_consecutive_days > (0)::numeric))),
    CONSTRAINT chk_leave_type_notice CHECK ((min_notice_calendar_days >= 0))
);


--
-- Name: leave_types_leave_type_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.leave_types ALTER COLUMN leave_type_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.leave_types_leave_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permissions (
    permission_id bigint NOT NULL,
    permission_code character varying(100) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: permissions_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.permissions ALTER COLUMN permission_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.permissions_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: public_holidays; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.public_holidays (
    public_holiday_id bigint NOT NULL,
    holiday_date date NOT NULL,
    holiday_name character varying(150) NOT NULL,
    country_code character varying(2) DEFAULT 'AE'::character varying NOT NULL,
    region character varying(100) DEFAULT 'all'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: public_holidays_public_holiday_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.public_holidays ALTER COLUMN public_holiday_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.public_holidays_public_holiday_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    role_id bigint NOT NULL,
    permission_id bigint NOT NULL
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    role_id bigint NOT NULL,
    role_name character varying(50) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: roles_role_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.roles ALTER COLUMN role_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.roles_role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    migration_id bigint NOT NULL,
    migration_version character varying(100) NOT NULL,
    description character varying(255) NOT NULL,
    checksum character varying(64) NOT NULL,
    applied_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    execution_time_ms bigint,
    CONSTRAINT chk_migration_execution_time CHECK (((execution_time_ms IS NULL) OR (execution_time_ms >= 0)))
);


--
-- Name: schema_migrations_migration_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.schema_migrations ALTER COLUMN migration_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.schema_migrations_migration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: timesheet_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.timesheet_approvals (
    timesheet_approval_id bigint NOT NULL,
    timesheet_id bigint NOT NULL,
    approver_employee_id bigint NOT NULL,
    decision character varying(20) NOT NULL,
    comments text,
    decided_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_timesheet_approval_decision CHECK (((decision)::text = ANY ((ARRAY['approved'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Name: timesheet_approvals_timesheet_approval_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.timesheet_approvals ALTER COLUMN timesheet_approval_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.timesheet_approvals_timesheet_approval_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: timesheet_entries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.timesheet_entries (
    timesheet_entry_id bigint NOT NULL,
    timesheet_id bigint NOT NULL,
    work_date date NOT NULL,
    hours_worked numeric(5,2) NOT NULL,
    task_description text,
    project_code character varying(100),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_timesheet_entry_hours CHECK (((hours_worked >= (0)::numeric) AND (hours_worked <= (24)::numeric)))
);


--
-- Name: timesheet_entries_timesheet_entry_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.timesheet_entries ALTER COLUMN timesheet_entry_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.timesheet_entries_timesheet_entry_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: timesheets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.timesheets (
    timesheet_id bigint NOT NULL,
    employee_id bigint NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    submitted_at timestamp with time zone,
    approved_at timestamp with time zone,
    total_hours numeric(7,2) DEFAULT 0 NOT NULL,
    employee_comments text,
    reviewer_comments text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_timesheet_period CHECK (((period_end >= period_start) AND ((period_end - period_start) = 6))),
    CONSTRAINT chk_timesheet_status CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'submitted'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[]))),
    CONSTRAINT chk_timesheet_total_hours CHECK ((total_hours >= (0)::numeric))
);


--
-- Name: timesheets_timesheet_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.timesheets ALTER COLUMN timesheet_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.timesheets_timesheet_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    user_id bigint NOT NULL,
    role_id bigint NOT NULL,
    assigned_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    employee_id bigint,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.users ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ai_conversations ai_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_conversations
    ADD CONSTRAINT ai_conversations_pkey PRIMARY KEY (conversation_id);


--
-- Name: ai_messages ai_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_messages
    ADD CONSTRAINT ai_messages_pkey PRIMARY KEY (message_id);


--
-- Name: ai_tool_executions ai_tool_executions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_tool_executions
    ADD CONSTRAINT ai_tool_executions_pkey PRIMARY KEY (tool_execution_id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (audit_log_id);


--
-- Name: departments departments_department_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_department_code_key UNIQUE (department_code);


--
-- Name: departments departments_department_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_department_name_key UNIQUE (department_name);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (department_id);


--
-- Name: employees employees_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_email_key UNIQUE (email);


--
-- Name: employees employees_employee_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_employee_code_key UNIQUE (employee_code);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (employee_id);


--
-- Name: hr_document_request_history hr_document_request_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_request_history
    ADD CONSTRAINT hr_document_request_history_pkey PRIMARY KEY (history_id);


--
-- Name: hr_document_requests hr_document_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_requests
    ADD CONSTRAINT hr_document_requests_pkey PRIMARY KEY (document_request_id);


--
-- Name: hr_document_types hr_document_types_document_type_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_types
    ADD CONSTRAINT hr_document_types_document_type_code_key UNIQUE (document_type_code);


--
-- Name: hr_document_types hr_document_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_types
    ADD CONSTRAINT hr_document_types_pkey PRIMARY KEY (document_type_id);


--
-- Name: hr_policies hr_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policies
    ADD CONSTRAINT hr_policies_pkey PRIMARY KEY (policy_id);


--
-- Name: hr_policies hr_policies_policy_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policies
    ADD CONSTRAINT hr_policies_policy_code_key UNIQUE (policy_code);


--
-- Name: hr_policy_chunks hr_policy_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_chunks
    ADD CONSTRAINT hr_policy_chunks_pkey PRIMARY KEY (policy_chunk_id);


--
-- Name: hr_policy_versions hr_policy_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_versions
    ADD CONSTRAINT hr_policy_versions_pkey PRIMARY KEY (policy_version_id);


--
-- Name: leave_approvals leave_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_approvals
    ADD CONSTRAINT leave_approvals_pkey PRIMARY KEY (leave_approval_id);


--
-- Name: leave_balances leave_balances_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_balances
    ADD CONSTRAINT leave_balances_pkey PRIMARY KEY (leave_balance_id);


--
-- Name: leave_entitlement_rules leave_entitlement_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_entitlement_rules
    ADD CONSTRAINT leave_entitlement_rules_pkey PRIMARY KEY (entitlement_rule_id);


--
-- Name: leave_requests leave_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT leave_requests_pkey PRIMARY KEY (leave_request_id);


--
-- Name: leave_transactions leave_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_transactions
    ADD CONSTRAINT leave_transactions_pkey PRIMARY KEY (leave_transaction_id);


--
-- Name: leave_types leave_types_leave_type_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_types
    ADD CONSTRAINT leave_types_leave_type_code_key UNIQUE (leave_type_code);


--
-- Name: leave_types leave_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_types
    ADD CONSTRAINT leave_types_pkey PRIMARY KEY (leave_type_id);


--
-- Name: permissions permissions_permission_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_permission_code_key UNIQUE (permission_code);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (permission_id);


--
-- Name: public_holidays public_holidays_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_holidays
    ADD CONSTRAINT public_holidays_pkey PRIMARY KEY (public_holiday_id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (role_id);


--
-- Name: roles roles_role_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_role_name_key UNIQUE (role_name);


--
-- Name: schema_migrations schema_migrations_migration_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_migration_version_key UNIQUE (migration_version);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (migration_id);


--
-- Name: timesheet_approvals timesheet_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheet_approvals
    ADD CONSTRAINT timesheet_approvals_pkey PRIMARY KEY (timesheet_approval_id);


--
-- Name: timesheet_entries timesheet_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheet_entries
    ADD CONSTRAINT timesheet_entries_pkey PRIMARY KEY (timesheet_entry_id);


--
-- Name: timesheets timesheets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT timesheets_pkey PRIMARY KEY (timesheet_id);


--
-- Name: leave_balances uq_employee_leave_year; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_balances
    ADD CONSTRAINT uq_employee_leave_year UNIQUE (employee_id, leave_type, balance_year);


--
-- Name: hr_policy_chunks uq_hr_policy_chunk_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_chunks
    ADD CONSTRAINT uq_hr_policy_chunk_number UNIQUE (policy_version_id, chunk_number);


--
-- Name: hr_policy_versions uq_hr_policy_version_number; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_versions
    ADD CONSTRAINT uq_hr_policy_version_number UNIQUE (policy_id, version_number);


--
-- Name: public_holidays uq_public_holiday; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.public_holidays
    ADD CONSTRAINT uq_public_holiday UNIQUE (holiday_date, country_code, region);


--
-- Name: timesheets uq_timesheet_employee_period; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT uq_timesheet_employee_period UNIQUE (employee_id, period_start);


--
-- Name: timesheet_entries uq_timesheet_work_date; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheet_entries
    ADD CONSTRAINT uq_timesheet_work_date UNIQUE (timesheet_id, work_date);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_employee_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_employee_id_key UNIQUE (employee_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: idx_ai_conversations_user_recent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_conversations_user_recent ON public.ai_conversations USING btree (user_id, started_at DESC);


--
-- Name: idx_ai_messages_conversation_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_messages_conversation_time ON public.ai_messages USING btree (conversation_id, created_at);


--
-- Name: idx_ai_tool_executions_conversation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_tool_executions_conversation ON public.ai_tool_executions USING btree (conversation_id, started_at DESC);


--
-- Name: idx_ai_tool_executions_message; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_tool_executions_message ON public.ai_tool_executions USING btree (message_id) WHERE (message_id IS NOT NULL);


--
-- Name: idx_ai_tool_executions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_tool_executions_status ON public.ai_tool_executions USING btree (execution_status, started_at DESC);


--
-- Name: idx_ai_tool_executions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ai_tool_executions_user ON public.ai_tool_executions USING btree (user_id, started_at DESC);


--
-- Name: idx_audit_logs_actor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_actor ON public.audit_logs USING btree (actor_user_id);


--
-- Name: idx_audit_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_created_at ON public.audit_logs USING btree (created_at);


--
-- Name: idx_audit_logs_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_entity ON public.audit_logs USING btree (entity_type, entity_id);


--
-- Name: idx_departments_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_departments_parent ON public.departments USING btree (parent_department_id) WHERE (parent_department_id IS NOT NULL);


--
-- Name: idx_document_history_actor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_history_actor ON public.hr_document_request_history USING btree (action_by_user_id) WHERE (action_by_user_id IS NOT NULL);


--
-- Name: idx_document_history_request; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_history_request ON public.hr_document_request_history USING btree (document_request_id, action_at DESC);


--
-- Name: idx_document_requests_employee_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_requests_employee_status ON public.hr_document_requests USING btree (employee_id, status);


--
-- Name: idx_document_requests_processor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_requests_processor ON public.hr_document_requests USING btree (processed_by_employee_id) WHERE (processed_by_employee_id IS NOT NULL);


--
-- Name: idx_document_requests_requested_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_requests_requested_at ON public.hr_document_requests USING btree (requested_at DESC);


--
-- Name: idx_document_requests_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_document_requests_type ON public.hr_document_requests USING btree (document_type);


--
-- Name: idx_employees_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employees_department ON public.employees USING btree (department_id);


--
-- Name: idx_employees_manager; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_employees_manager ON public.employees USING btree (manager_employee_id);


--
-- Name: idx_entitlement_rules_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entitlement_rules_lookup ON public.leave_entitlement_rules USING btree (leave_type_id, employment_category, effective_from);


--
-- Name: idx_hr_policies_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policies_category ON public.hr_policies USING btree (policy_category);


--
-- Name: idx_hr_policies_department; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policies_department ON public.hr_policies USING btree (department_id);


--
-- Name: idx_hr_policies_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policies_owner ON public.hr_policies USING btree (owner_user_id) WHERE (owner_user_id IS NOT NULL);


--
-- Name: idx_hr_policies_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policies_status ON public.hr_policies USING btree (status);


--
-- Name: idx_hr_policy_chunks_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_chunks_embedding_hnsw ON public.hr_policy_chunks USING hnsw (embedding public.halfvec_cosine_ops) WITH (m='16', ef_construction='64') WHERE (embedding IS NOT NULL);


--
-- Name: idx_hr_policy_chunks_search_vector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_chunks_search_vector ON public.hr_policy_chunks USING gin (search_vector);


--
-- Name: idx_hr_policy_chunks_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_chunks_version ON public.hr_policy_chunks USING btree (policy_version_id);


--
-- Name: idx_hr_policy_versions_approver; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_versions_approver ON public.hr_policy_versions USING btree (approved_by_user_id) WHERE (approved_by_user_id IS NOT NULL);


--
-- Name: idx_hr_policy_versions_creator; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_versions_creator ON public.hr_policy_versions USING btree (created_by_user_id) WHERE (created_by_user_id IS NOT NULL);


--
-- Name: idx_hr_policy_versions_effective_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_versions_effective_dates ON public.hr_policy_versions USING btree (effective_from, effective_to);


--
-- Name: idx_hr_policy_versions_policy; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_versions_policy ON public.hr_policy_versions USING btree (policy_id, version_number DESC);


--
-- Name: idx_hr_policy_versions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hr_policy_versions_status ON public.hr_policy_versions USING btree (status);


--
-- Name: idx_leave_approvals_approver; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_approvals_approver ON public.leave_approvals USING btree (approver_employee_id);


--
-- Name: idx_leave_approvals_request; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_approvals_request ON public.leave_approvals USING btree (leave_request_id, decided_at DESC);


--
-- Name: idx_leave_balances_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_balances_type ON public.leave_balances USING btree (leave_type);


--
-- Name: idx_leave_requests_dates; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_requests_dates ON public.leave_requests USING btree (start_date, end_date);


--
-- Name: idx_leave_requests_employee_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_requests_employee_status ON public.leave_requests USING btree (employee_id, status);


--
-- Name: idx_leave_requests_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_requests_type ON public.leave_requests USING btree (leave_type);


--
-- Name: idx_leave_transactions_actor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_transactions_actor ON public.leave_transactions USING btree (actor_user_id) WHERE (actor_user_id IS NOT NULL);


--
-- Name: idx_leave_transactions_balance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_transactions_balance ON public.leave_transactions USING btree (leave_balance_id, created_at DESC);


--
-- Name: idx_leave_transactions_employee; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_transactions_employee ON public.leave_transactions USING btree (employee_id, created_at DESC);


--
-- Name: idx_leave_transactions_request; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_leave_transactions_request ON public.leave_transactions USING btree (leave_request_id) WHERE (leave_request_id IS NOT NULL);


--
-- Name: idx_public_holidays_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_public_holidays_date ON public.public_holidays USING btree (holiday_date) WHERE (is_active = true);


--
-- Name: idx_role_permissions_permission; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_role_permissions_permission ON public.role_permissions USING btree (permission_id);


--
-- Name: idx_timesheet_approvals_approver; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timesheet_approvals_approver ON public.timesheet_approvals USING btree (approver_employee_id);


--
-- Name: idx_timesheet_approvals_timesheet; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timesheet_approvals_timesheet ON public.timesheet_approvals USING btree (timesheet_id, decided_at DESC);


--
-- Name: idx_timesheet_entries_work_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timesheet_entries_work_date ON public.timesheet_entries USING btree (work_date);


--
-- Name: idx_timesheets_employee_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timesheets_employee_status ON public.timesheets USING btree (employee_id, status);


--
-- Name: idx_timesheets_period; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_timesheets_period ON public.timesheets USING btree (period_start, period_end);


--
-- Name: idx_user_roles_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_roles_role ON public.user_roles USING btree (role_id);


--
-- Name: ai_conversations ai_conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_conversations
    ADD CONSTRAINT ai_conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: ai_messages ai_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_messages
    ADD CONSTRAINT ai_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.ai_conversations(conversation_id) ON DELETE CASCADE;


--
-- Name: ai_tool_executions ai_tool_executions_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_tool_executions
    ADD CONSTRAINT ai_tool_executions_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.ai_conversations(conversation_id);


--
-- Name: ai_tool_executions ai_tool_executions_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_tool_executions
    ADD CONSTRAINT ai_tool_executions_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.ai_messages(message_id);


--
-- Name: ai_tool_executions ai_tool_executions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_tool_executions
    ADD CONSTRAINT ai_tool_executions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: audit_logs audit_logs_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: departments departments_parent_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_parent_department_id_fkey FOREIGN KEY (parent_department_id) REFERENCES public.departments(department_id);


--
-- Name: hr_document_requests fk_document_requests_type_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_requests
    ADD CONSTRAINT fk_document_requests_type_code FOREIGN KEY (document_type) REFERENCES public.hr_document_types(document_type_code);


--
-- Name: employees fk_employees_department; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT fk_employees_department FOREIGN KEY (department_id) REFERENCES public.departments(department_id);


--
-- Name: employees fk_employees_manager; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT fk_employees_manager FOREIGN KEY (manager_employee_id) REFERENCES public.employees(employee_id);


--
-- Name: leave_balances fk_leave_balances_type_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_balances
    ADD CONSTRAINT fk_leave_balances_type_code FOREIGN KEY (leave_type) REFERENCES public.leave_types(leave_type_code);


--
-- Name: leave_requests fk_leave_requests_type_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT fk_leave_requests_type_code FOREIGN KEY (leave_type) REFERENCES public.leave_types(leave_type_code);


--
-- Name: hr_document_request_history hr_document_request_history_action_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_request_history
    ADD CONSTRAINT hr_document_request_history_action_by_user_id_fkey FOREIGN KEY (action_by_user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: hr_document_request_history hr_document_request_history_document_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_request_history
    ADD CONSTRAINT hr_document_request_history_document_request_id_fkey FOREIGN KEY (document_request_id) REFERENCES public.hr_document_requests(document_request_id);


--
-- Name: hr_document_requests hr_document_requests_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_requests
    ADD CONSTRAINT hr_document_requests_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id);


--
-- Name: hr_document_requests hr_document_requests_processed_by_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_document_requests
    ADD CONSTRAINT hr_document_requests_processed_by_employee_id_fkey FOREIGN KEY (processed_by_employee_id) REFERENCES public.employees(employee_id);


--
-- Name: hr_policies hr_policies_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policies
    ADD CONSTRAINT hr_policies_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(department_id) ON DELETE SET NULL;


--
-- Name: hr_policies hr_policies_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policies
    ADD CONSTRAINT hr_policies_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: hr_policy_chunks hr_policy_chunks_policy_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_chunks
    ADD CONSTRAINT hr_policy_chunks_policy_version_id_fkey FOREIGN KEY (policy_version_id) REFERENCES public.hr_policy_versions(policy_version_id) ON DELETE RESTRICT;


--
-- Name: hr_policy_versions hr_policy_versions_approved_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_versions
    ADD CONSTRAINT hr_policy_versions_approved_by_user_id_fkey FOREIGN KEY (approved_by_user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: hr_policy_versions hr_policy_versions_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_versions
    ADD CONSTRAINT hr_policy_versions_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: hr_policy_versions hr_policy_versions_policy_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hr_policy_versions
    ADD CONSTRAINT hr_policy_versions_policy_id_fkey FOREIGN KEY (policy_id) REFERENCES public.hr_policies(policy_id) ON DELETE RESTRICT;


--
-- Name: leave_approvals leave_approvals_approver_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_approvals
    ADD CONSTRAINT leave_approvals_approver_employee_id_fkey FOREIGN KEY (approver_employee_id) REFERENCES public.employees(employee_id);


--
-- Name: leave_approvals leave_approvals_leave_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_approvals
    ADD CONSTRAINT leave_approvals_leave_request_id_fkey FOREIGN KEY (leave_request_id) REFERENCES public.leave_requests(leave_request_id);


--
-- Name: leave_balances leave_balances_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_balances
    ADD CONSTRAINT leave_balances_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id);


--
-- Name: leave_entitlement_rules leave_entitlement_rules_leave_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_entitlement_rules
    ADD CONSTRAINT leave_entitlement_rules_leave_type_id_fkey FOREIGN KEY (leave_type_id) REFERENCES public.leave_types(leave_type_id);


--
-- Name: leave_requests leave_requests_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_requests
    ADD CONSTRAINT leave_requests_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id);


--
-- Name: leave_transactions leave_transactions_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_transactions
    ADD CONSTRAINT leave_transactions_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.users(user_id) ON DELETE SET NULL;


--
-- Name: leave_transactions leave_transactions_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_transactions
    ADD CONSTRAINT leave_transactions_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id);


--
-- Name: leave_transactions leave_transactions_leave_balance_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_transactions
    ADD CONSTRAINT leave_transactions_leave_balance_id_fkey FOREIGN KEY (leave_balance_id) REFERENCES public.leave_balances(leave_balance_id);


--
-- Name: leave_transactions leave_transactions_leave_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.leave_transactions
    ADD CONSTRAINT leave_transactions_leave_request_id_fkey FOREIGN KEY (leave_request_id) REFERENCES public.leave_requests(leave_request_id);


--
-- Name: role_permissions role_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES public.permissions(permission_id) ON DELETE CASCADE;


--
-- Name: role_permissions role_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(role_id) ON DELETE CASCADE;


--
-- Name: timesheet_approvals timesheet_approvals_approver_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheet_approvals
    ADD CONSTRAINT timesheet_approvals_approver_employee_id_fkey FOREIGN KEY (approver_employee_id) REFERENCES public.employees(employee_id);


--
-- Name: timesheet_approvals timesheet_approvals_timesheet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheet_approvals
    ADD CONSTRAINT timesheet_approvals_timesheet_id_fkey FOREIGN KEY (timesheet_id) REFERENCES public.timesheets(timesheet_id);


--
-- Name: timesheet_entries timesheet_entries_timesheet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheet_entries
    ADD CONSTRAINT timesheet_entries_timesheet_id_fkey FOREIGN KEY (timesheet_id) REFERENCES public.timesheets(timesheet_id) ON DELETE CASCADE;


--
-- Name: timesheets timesheets_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.timesheets
    ADD CONSTRAINT timesheets_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id);


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(role_id) ON DELETE CASCADE;


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: users users_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(employee_id);


--
-- PostgreSQL database dump complete
--