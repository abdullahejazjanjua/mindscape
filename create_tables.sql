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

-- 5. COMMENTS TABLE (weak entity, with recursive FK)
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

-- 6. REPORTS TABLE (weak entity)
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


