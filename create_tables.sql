-- 1. USER TABLE
CREATE TABLE USERS (
    UserID SERIAL PRIMARY KEY,
    Name VARCHAR(100),
    Username VARCHAR(50) UNIQUE,
    Email VARCHAR(100) UNIQUE,
    Password VARCHAR(100)
);

-- 2. USER_MOD TABLE (no MOD table anymore)
CREATE TABLE USER_MOD (
    UserID INT,
    ModID INT,
    PRIMARY KEY (UserID, ModID),
    FOREIGN KEY (UserID) REFERENCES USERS(UserID)
);

-- 3. BOARD TABLE
CREATE TABLE BOARD (
    BoardID SERIAL PRIMARY KEY,
    Theme VARCHAR(100),
    Date_Created DATE
);

-- 4. MOD_BOARD TABLE
CREATE TABLE MOD_BOARD (
    UserID INT,
    ModID INT,
    BoardID INT,
    PRIMARY KEY (UserID, ModID, BoardID),
    FOREIGN KEY (UserID, ModID) REFERENCES USER_MOD(UserID, ModID),
    FOREIGN KEY (BoardID) REFERENCES BOARD(BoardID)
);

CREATE TABLE COMMENTS (
    CommentID INT,
    BoardID INT,
    Text TEXT,
    Date TIMESTAMP,
    UserID INT,
    ParentCommentID INT,
    PRIMARY KEY (CommentID, BoardID),
    FOREIGN KEY (UserID) REFERENCES USERS(UserID),
    FOREIGN KEY (BoardID) REFERENCES BOARD(BoardID),
    FOREIGN KEY (ParentCommentID, BoardID) REFERENCES COMMENTS(CommentID, BoardID)
);

CREATE TABLE REPORTS (
    ReportID INT,
    UserID INT,
    Text TEXT,
    IO BOOLEAN,
    PRIMARY KEY (ReportID, UserID),
    FOREIGN KEY (UserID) REFERENCES USERS(UserID)
);


INSERT INTO USERS (Name, Username, Email, Password) VALUES
('Alice', 'alice123', 'alice@example.com', 'pass1');

SELECT username, email, password FROM USERS WHERE username = 'alice123';

SELECT * FROM Board;

INSERT INTO USERS (Name, Username, Email, Password) VALUES
('Bob', 'bob321', 'bob@example.com', 'pass2'),
('Carol', 'carol456', 'carol@example.com', 'pass3');

-- INSERT INTO USER_MOD (UserID, ModID) VALUES
-- (1, 101),
-- (2, 102);

-- Insert BOARDs
INSERT INTO BOARD (Theme, Date_Created) VALUES
('Technology', '2024-01-01'),
('Gaming', '2024-02-15');

-- Insert MOD_BOARD (Alice moderates Tech, Bob moderates Gaming)
INSERT INTO MOD_BOARD (UserID, ModID, BoardID) VALUES
(1, 101, 1),
(2, 102, 2);

-- Insert COMMENTS
INSERT INTO COMMENTS (CommentID, BoardID, Text, Date, UserID, ParentCommentID) VALUES
(1, 1, 'Welcome to Tech board!', '2025-01-01 10:00:00', 1, NULL),
(2, 1, 'Thanks! Glad to be here.', '2025-01-01 10:05:00', 2, 1),
(3, 2, 'Anyone playing Elden Ring?', '2025-01-10 15:30:00', 2, NULL);

-- Insert REPORTS
INSERT INTO REPORTS (ReportID, UserID, Text, IO) VALUES
(1, 1, 'Spam in comments', TRUE),
(2, 2, 'Offensive language', FALSE);
