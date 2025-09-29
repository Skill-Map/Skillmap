
CREATE TABLE USERS(
	id UUID PRIMARY KEY,
	email VARCHAR(255),
	password_hash TEXT,
	is_active BOOLEAN,
	created_at TIMESTAMP,
	updated_at TIMESTAMP
);

CREATE TABLE ROLES(
	id SERIAL PRIMARY KEY,
	code VARCHAR(64),
	name VARCHAR(255)
);

CREATE TABLE USER_ROLES(
	user_id UUID REFERENCES USERS(id),
	role_id INT REFERENCES ROLES(id)
);

CREATE TABLE CONSENTS(
	id UUID PRIMARY KEY,
	user_id UUID REFERENCES USERS(id),
	type VARCHAR(64),
	given_at TIMESTAMP,
	revoked BOOLEAN
);

CREATE TABLE AUTH_ATTEMPTS(
	id	BIGSERIAL PRIMARY KEY,
	email VARCHAR(255),
	succeeded BOOLEAN,
	ip INET,
	created_at TIMESTAMP
);


CREATE TABLE SKILLS(
	id	UUID PRIMARY KEY,
	code	VARCHAR(64),
	name	VARCHAR(255),
	description	TEXT,
	level_max	SMALLINT,
	is_active	BOOLEAN,
	created_at	TIMESTAMP
);

CREATE TABLE SKILLS_EDGES(
	id	UUID PRIMARY KEY,
	from_skill_id	UUID REFERENCES SKILLS(id),
	to_skill_id	UUID REFERENCES SKILLS(id),
	edge_type	VARCHAR(32)
);

CREATE TABLE TRACK_SKILL_MAP(
	id	UUID PRIMARY KEY,
	track_id	VARCHAR(64),
	skill_id	UUID,
	order_index	SMALLINT
);

CREATE TABLE STUDENT_PROFILE(
	id	UUID PRIMARY KEY,
	user_id	UUID REFERENCES USERS(id) UNIQUE,
	created_at	TIMESTAMP,
	updated_at	TIMESTAMP,
	is_active	BOOLEAN,
	status	VARCHAR(32),
	track_id	VARCHAR(64),
	group_code	VARCHAR(64),
	advisor_user_id	UUID REFERENCES USERS(id),
	enrollment_date	DATE,
	expected_graduation	DATE,
	hours_per_week	SMALLINT,
	progress_percent	NUMERIC(5,2),
	credits_earned	NUMERIC(6,2)
);

CREATE TABLE TEACHER_PROFILE(
	id	UUID PRIMARY KEY,
	user_id	UUID REFERENCES USERS(id) UNIQUE,
	created_at	TIMESTAMP,
	updated_at	TIMESTAMP,
	is_active	BOOLEAN,
	hire_date	DATE,
	department	VARCHAR(128),
	title	VARCHAR(64),
	bio	TEXT,
	specialties	TEXT,
	office_hours	VARCHAR(128),
	hours_per_week	SMALLINT,
	rating	NUMERIC(3,2)
);

CREATE TABLE MODERATOR_PROFILE(
	id	UUID PRIMARY KEY,
	user_id	UUID REFERENCES USERS(id) UNIQUE,
	created_at	TIMESTAMP,
	updated_at	TIMESTAMP,
	is_active	BOOLEAN,
	assigned_scope	VARCHAR(128),
	permissions_scope	JSONB,
	on_call	BOOLEAN,
	last_action_at	TIMESTAMP,
	warnings_issued	INT,
	users_banned	INT
);

CREATE TABLE ADMIN_PROFILE(
	id	UUID PRIMARY KEY,
	user_id	UUID REFERENCES USERS(id) UNIQUE,
	created_at	TIMESTAMP,
	updated_at	TIMESTAMP,
	is_active	BOOLEAN,
	super_permissions	JSONB,
	can_manage_roles	BOOLEAN,
	can_manage_billing	BOOLEAN,
	can_impersonate	BOOLEAN,
	last_audit_action	TIMESTAMP,
	security_training_at	DATE
);




