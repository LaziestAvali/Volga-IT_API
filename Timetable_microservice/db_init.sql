CREATE TABLE IF NOT EXISTS public.timetables
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    hospitalId bigint NOT NULL,
    doctorId bigint NOT NULL,
    "start" timestamp without time zone NOT NULL,
    "to" timestamp without time zone NOT NULL,
    room character varying(50) NOT NULL,
    is_disabled boolean NOT NULL DEFAULT false,
    CONSTRAINT timetables_pkey PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.appointment
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    timetable_id bigint NOT NULL,
    account_id bigint NOT NULL,
    "time" timestamp without time zone NOT NULL,
    is_disabled boolean NOT NULL,
    CONSTRAINT appointment_pkey PRIMARY KEY (id),
    CONSTRAINT "timetables_FK" FOREIGN KEY (timetable_id)
        REFERENCES public.timetables (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        NOT VALID
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.timetables
    OWNER to accountadmin;

ALTER TABLE IF EXISTS public.appointment
    OWNER to accountadmin;