from js import db
from pyodide.ffi import to_js

class Database:
    def run(self, sql, params=None):
        if params:
            stmt = db.prepare(sql)
            for i, p in enumerate(params):
                stmt.bind([p] if not isinstance(p, list) else p)
            stmt.step()
            stmt.free()
        else:
            db.run(sql)

    def query(self, sql, params=None):
        if params:
            stmt = db.prepare(sql)
            stmt.bind(params)
            rows = []
            while stmt.step():
                rows.append(stmt.getAsObject())
            stmt.free()
            return rows
        else:
            result = db.exec(sql)
            if result:
                return result[0].values
            return []

    def add_user(self, name, email, alter_):
        existing = self.query("SELECT id FROM users WHERE email = ?", [email])
        if existing:
            return existing[0]["id"]

        self.run(
            "INSERT INTO users (name, email, alter_) VALUES (?, ?, ?)",
            [name, email, alter_]
        )
        return self.query("SELECT last_insert_rowid() AS id")[0]["id"]

    def login(self, email):
        result = self.query(
            "SELECT id, name, email, alter_ FROM users WHERE email = ?",
            [email]
        )
        return result[0] if result else None

    def add_movie(self, title, genre, release_year):
        self.run(
            "INSERT INTO movies (title, genre, release_year) VALUES (?, ?, ?)",
            [title, genre, release_year]
        )
        return self.query("SELECT last_insert_rowid() AS id")[0]["id"]

    def search_movies(self, keyword):
        return self.query(
            """
            SELECT movies.id, movies.title, movies.genre, movies.release_year,
                   (SELECT AVG(rating) FROM ratings WHERE movie_id = movies.id) AS avg_rating
            FROM movies
            WHERE movies.title LIKE ? OR movies.genre LIKE ?
            """,
            [f"%{keyword}%", f"%{keyword}%"]
        )

    def get_movie_description(self, movie_id):
        result = self.query("SELECT shorty FROM movies WHERE id = ?", [movie_id])
        return result[0]["shorty"] if result else None

    def get_all_titles(self):
        rows = self.query("SELECT title FROM movies")
        return [r["title"] for r in rows]

    def add_rating(self, user_id, movie_id, rating):
        self.run(
            "INSERT INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)",
            [user_id, movie_id, rating]
        )

    def add_to_watchlist(self, user_id, movie_id):
        self.run(
            "INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)",
            [user_id, movie_id]
        )

    def get_watchlist(self, user_id):
        return self.query(
            """
            SELECT movies.id, movies.title, movies.genre, movies.release_year
            FROM movies
            JOIN watchlist ON movies.id = watchlist.movie_id
            WHERE watchlist.user_id = ?
            """,
            [user_id]
        )

    def get_stats(self, user_id):
        total_movies = self.query("SELECT COUNT(*) AS c FROM movies")[0]["c"]
        user_ratings = self.query("SELECT COUNT(*) AS c FROM ratings WHERE user_id = ?", [user_id])[0]["c"]
        watchlist_size = self.query("SELECT COUNT(*) AS c FROM watchlist WHERE user_id = ?", [user_id])[0]["c"]
        avg_rating = self.query("SELECT AVG(rating) AS a FROM ratings WHERE user_id = ?", [user_id])[0]["a"] or 0.0

        return {
            "total_movies": total_movies,
            "user_ratings": user_ratings,
            "watchlist_size": watchlist_size,
            "avg_rating": round(avg_rating, 1)
        }

    def add_description(self, movie_id, description):
        self.run(
            "UPDATE movies SET shorty = ? WHERE id = ?",
            [description, movie_id]
        )


# Demo-Ausgabe
dbase = Database()
dbase.add_movie("Matrix", "Sci-Fi", 1999)

from js import document
document.getElementById("output").innerHTML = "MovieCrusher läuft im Browser!"
