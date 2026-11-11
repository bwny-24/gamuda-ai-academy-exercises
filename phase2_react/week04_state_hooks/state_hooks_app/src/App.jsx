import SecretMessage from './Components/SecretMessage'

// Week 4 exercises live in src/Components. To add one:
//   1. create src/Components/MyExercise.jsx
//   2. import it here and add it inside <main> below
function App() {
  return (
    <main style={{ padding: '24px', textAlign: 'left' }}>
      <h1>Week 4 : State &amp; Hooks</h1>

      <section>
        <h2>useState : show / hide</h2>
        <SecretMessage />
      </section>
    </main>
  )
}

export default App
