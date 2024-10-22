CREATE TABLE IF NOT EXISTS public.account
(
    id integer NOT NULL DEFAULT nextval('account_id_seq'::regclass),
    login character varying(20) COLLATE pg_catalog."default" NOT NULL,
    password character varying(50) COLLATE pg_catalog."default" NOT NULL,
    "firstName" character varying(50) COLLATE pg_catalog."default" NOT NULL,
    "lastName" character varying(50) COLLATE pg_catalog."default" NOT NULL,
    is_disabled boolean NOT NULL,
    CONSTRAINT account_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.account
    OWNER to accountadmin;

CREATE TABLE IF NOT EXISTS public.role
(
    id integer NOT NULL DEFAULT nextval('role_id_seq'::regclass),
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT role_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.role
    OWNER to accountadmin;

CREATE TABLE IF NOT EXISTS public.account_role
(
    id integer NOT NULL DEFAULT nextval('account_role_id_seq'::regclass),
    account_id integer NOT NULL,
    role_id integer NOT NULL,
    CONSTRAINT account_role_pkey PRIMARY KEY (id),
    CONSTRAINT "account_FK" FOREIGN KEY (account_id)
        REFERENCES public.account (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID,
    CONSTRAINT "role_FK" FOREIGN KEY (role_id)
        REFERENCES public.role (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.account_role
    OWNER to accountadmin;

CREATE TABLE IF NOT EXISTS public.tokens
(
    id integer NOT NULL DEFAULT nextval('tokens_id_seq'::regclass),
    account_id integer NOT NULL,
    token character varying(200) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT tokens_pkey PRIMARY KEY (id),
    CONSTRAINT "account_FK" FOREIGN KEY (account_id)
        REFERENCES public.account (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.tokens
    OWNER to accountadmin;

INSERT INTO public.account(login, password, "firstName", "lastName", is_disabled)
VALUES
(admin, c7ad44cbad762a5da0a452f9e854fdc1e0e7a52a38015f23f3eab1d80b931dd472634dfac71cd34ebc35d16ab7fb8a90c81f975113d6c7538dc69dd8de9077ec, admin, admin, false),
(manager, 5fc2ca6f085919f2f77626f1e280fab9cc92b4edc9edc53ac6eee3f72c5c508e869ee9d67a96d63986d14c1c2b82c35ff5f31494bea831015424f59c96fff664, manager, manager, false),
(doctor, 10af4e2a428d75aa00745efbaac308b17fb047373820988172eefdc4d747d3a23bfb81eb511912e6e1399d576ef0da2cb9af44dfc79caf63a3f2aa5ab7eab53c, doctor, doctor, false),
(user, b14361404c078ffd549c03db443c3fede2f3e534d73f78f77301ed97d4a436a9fd9db05ee8b325c0ad36438b43fec8510c204fc1c1edb21d0941c00e9e2c1ce2, user, user, false);

INSERT INTO public.role(name)
VALUES
(admin),
(manager),
(doctor),
(user);

INSERT INTO public.account_role(account_id, role_id)
VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4);
