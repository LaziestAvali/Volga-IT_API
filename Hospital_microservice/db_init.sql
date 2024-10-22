CREATE TABLE IF NOT EXISTS public.hospitals
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    address character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "contactPhone" character varying(20) COLLATE pg_catalog."default" NOT NULL,
    is_disabled boolean NOT NULL DEFAULT false,
    CONSTRAINT hospitals_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.hospitals
    OWNER to hospitaladmin;

CREATE TABLE IF NOT EXISTS public.rooms
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1 ),
    hospital_id bigint NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT rooms_pkey PRIMARY KEY (id),
    CONSTRAINT "hospital_FK" FOREIGN KEY (hospital_id)
        REFERENCES public.hospitals (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.rooms
    OWNER to hospitaladmin;