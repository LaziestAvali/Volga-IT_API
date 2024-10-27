CREATE TABLE IF NOT EXISTS public.hospitals
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    address character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "contactPhone" character varying(20) COLLATE pg_catalog."default" NOT NULL,
    rooms character varying(50)[] COLLATE pg_catalog."default" NOT NULL,
    is_disabled boolean NOT NULL DEFAULT false,
    CONSTRAINT hospitals_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.hospitals
    OWNER to hospitaladmin;