CREATE TABLE public.users (
	user_id serial4 NOT NULL,
	username varchar(255) NOT NULL,
	password_hash varchar(255) NOT NULL,
	session_id varchar(255) NULL,
	CONSTRAINT users_pkey PRIMARY KEY (user_id),
	CONSTRAINT users_un UNIQUE (username)
);

CREATE TABLE public.trackers (
	tracker_id serial4 NOT NULL,
	alias varchar(255) NULL,
	description text NULL,
	user_id int4 NULL,
	tracker_type varchar(255) NOT NULL,
	timing_enabled bool NOT NULL,
	status varchar(255) NOT NULL,
	CONSTRAINT trackers_pkey PRIMARY KEY (tracker_id),
	CONSTRAINT trackers_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);

CREATE TABLE public.redirect_links (
	redirect_link_id serial4 NOT NULL,
	tracker_id int4 NULL,
	target_url text NOT NULL,
	CONSTRAINT redirect_links_pkey PRIMARY KEY (redirect_link_id),
	CONSTRAINT redirect_links_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES public.trackers(tracker_id)
);

CREATE TABLE public.tracker_records (
	record_id serial4 NOT NULL,
	tracker_id int4 NULL,
	access_time timestamp NOT NULL,
	access_ip inet NOT NULL,
	country varchar(255) NULL,
	city varchar(255) NULL,
	isp varchar(255) NULL,
	request_header text NULL,
	CONSTRAINT tracker_records_pkey PRIMARY KEY (record_id),
	CONSTRAINT tracker_records_tracker_id_fkey FOREIGN KEY (tracker_id) REFERENCES public.trackers(tracker_id)
);

CREATE TABLE public.timing_records (
	timing_record_id serial4 NOT NULL,
	record_id int4 NULL,
	last_access_time timestamp NOT NULL,
	redirect_count int4 NOT NULL,
	CONSTRAINT timing_records_pkey PRIMARY KEY (timing_record_id),
	CONSTRAINT timing_records_record_id_fkey FOREIGN KEY (record_id) REFERENCES public.tracker_records(record_id)
);

CREATE VIEW user_activity AS
SELECT 
    users.user_id, 
    users.username, 
    COUNT(DISTINCT trackers.tracker_id) AS tracker_count, 
    COUNT(DISTINCT tracker_records.record_id) AS record_count
FROM 
    users 
LEFT JOIN 
    trackers ON users.user_id = trackers.user_id
LEFT JOIN 
    tracker_records ON trackers.tracker_id = tracker_records.tracker_id
GROUP BY 
    users.user_id;
