CREATE TABLE IF NOT EXISTS public.history
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    "date" timestamp without time zone NOT NULL,
    "pacientId" bigint NOT NULL,
    "hospitalId" bigint NOT NULL,
    "doctorId" character varying(20) NOT NULL,
    room character varying(50) NOT NULL,
    "data" character varying(200) NOT NULL,
    CONSTRAINT history_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.history
    OWNER to historyadmin;