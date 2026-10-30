
import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [books, setBooks] = useState([]);

  const [formData, setFormData] = useState({
    title: "",
    author: "",
    published_year: "",
  });

  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState("");

  // GET: Retrieve all books
  const fetchAllBooks = async () => {
    try {
      const response = await axios.get(`${API_URL}/books`);
      setBooks(response.data);
      setError("");
    } catch (error) {
      console.error("Error fetching books:", error);
      setError("Unable to load books from the server.");
    }
  };

  useEffect(() => {
    fetchAllBooks();
  }, []);

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // POST: Create a book
  const createBook = async (e) => {
    e.preventDefault();

    try {
      await axios.post(`${API_URL}/books`, {
        title: formData.title,
        author: formData.author,
        published_year: parseInt(formData.published_year, 10),
      });

      setFormData({
        title: "",
        author: "",
        published_year: "",
      });

      await fetchAllBooks();
    } catch (error) {
      console.error("Error creating book:", error);
      alert("Error adding book");
    }
  };

  // PUT: Update an existing book
  const updateBook = async (e) => {
    e.preventDefault();

    try {
      await axios.put(`${API_URL}/books/${editingId}`, {
        title: formData.title,
        author: formData.author,
        published_year: parseInt(formData.published_year, 10),
      });

      setFormData({
        title: "",
        author: "",
        published_year: "",
      });

      setEditingId(null);
      await fetchAllBooks();
    } catch (error) {
      console.error("Error updating book:", error);
      alert("Error updating book");
    }
  };

  // DELETE: Remove a book
  const deleteBook = async (bookId) => {
    if (window.confirm("Are you sure you want to delete this book?")) {
      try {
        await axios.delete(`${API_URL}/books/${bookId}`);

        if (editingId === bookId) {
          cancelEdit();
        }

        await fetchAllBooks();
      } catch (error) {
        console.error("Error deleting book:", error);
        alert("Error deleting book");
      }
    }
  };

  // Fill the form with book data
  const editBook = (book) => {
    setEditingId(book.id);

    setFormData({
      title: book.title,
      author: book.author,
      published_year: String(book.published_year),
    });
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingId(null);
    setFormData({
      title: "",
      author: "",
      published_year: "",
    });
  };

  return (
    <div className="app">
      <h1>Books Management System</h1>
      <p>React + FastAPI + PostgreSQL</p>

      <h2>{editingId === null ? "Add New Book" : "Edit Book"}</h2>

      <form onSubmit={editingId === null ? createBook : updateBook}>
        <input
          type="text"
          name="title"
          placeholder="Book Title"
          value={formData.title}
          onChange={handleChange}
          minLength={3}
          required
        />

        <input
          type="text"
          name="author"
          placeholder="Author"
          value={formData.author}
          onChange={handleChange}
          minLength={3}
          required
        />

        <input
          type="number"
          name="published_year"
          placeholder="Published Year"
          value={formData.published_year}
          onChange={handleChange}
          min={1801}
          max={2026}
          required
        />

        <button type="submit">
          {editingId === null ? "Add Book" : "Update Book"}
        </button>

        {editingId !== null && (
          <button type="button" onClick={cancelEdit}>
            Cancel
          </button>
        )}
      </form>

      {error && <p role="alert">{error}</p>}

      <h2>Book List</h2>

      {books.length === 0 ? (
        <p>No books available.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Author</th>
              <th>Year</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {books.map((book) => (
              <tr key={book.id}>
                <td>{book.id}</td>
                <td>{book.title}</td>
                <td>{book.author}</td>
                <td>{book.published_year}</td>
                <td>
                  <button onClick={() => editBook(book)}>
                    Edit
                  </button>

                  <button onClick={() => deleteBook(book.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;
