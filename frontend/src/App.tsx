import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import PadaPage from './pages/PadaPage';
import SutraPage from './pages/SutraPage';
import BookmarksPage from './pages/BookmarksPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="pada/:padaSlug" element={<PadaPage />} />
          <Route path="pada/:padaSlug/sutra/:sutraNumber" element={<SutraPage />} />
          <Route path="bookmarks" element={<BookmarksPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
