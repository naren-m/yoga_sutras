import { Link } from 'react-router-dom';
import { PADAS } from '../types';

export default function HomePage() {
  return (
    <div className="space-y-8">
      {/* Hero section */}
      <section className="text-center py-8 bg-white rounded-xl shadow-sm">
        <h2 className="text-4xl md:text-5xl font-serif text-amber-900 mb-4">
          पातञ्जलयोगसूत्राणि
        </h2>
        <p className="text-xl text-amber-700 mb-2">Pātañjala Yoga Sūtrāṇi</p>
        <p className="text-gray-600 max-w-2xl mx-auto px-4">
          Explore the 196 sutras of Patanjali with interactive Sanskrit tools.
          Click on any word to see its dictionary definition and sandhi analysis.
        </p>
      </section>

      {/* Padas grid */}
      <section>
        <h3 className="text-xl font-semibold text-amber-900 mb-4">The Four Chapters (Padas)</h3>
        <div className="grid md:grid-cols-2 gap-4">
          {PADAS.map((pada, index) => (
            <Link
              key={pada.slug}
              to={`/pada/${pada.slug}`}
              className="block bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow border border-amber-100 hover:border-amber-300"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center text-amber-800 font-serif text-xl flex-shrink-0">
                  {index + 1}
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-amber-900">{pada.title}</h4>
                  <p className="text-gray-600 text-sm mt-1">{pada.description}</p>
                  <p className="text-amber-600 text-sm mt-2">{pada.sutraCount} sutras</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Quick start */}
      <section className="bg-amber-100 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-amber-900 mb-3">Getting Started</h3>
        <ul className="space-y-2 text-amber-800">
          <li className="flex items-start gap-2">
            <span className="text-amber-600">•</span>
            <span>Select a Pada above or use the navigation tabs</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600">•</span>
            <span>Click on any Sanskrit word to see its meaning</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600">•</span>
            <span>Compound words are automatically split for easier understanding</span>
          </li>
        </ul>
      </section>

      {/* Famous sutra preview */}
      <section className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-amber-900 mb-4">Featured Sutra</h3>
        <blockquote className="border-l-4 border-amber-400 pl-4">
          <p className="text-2xl font-serif text-amber-900 mb-2">योगश्चित्तवृत्तिनिरोधः</p>
          <p className="text-amber-700 italic mb-2">yogaś-citta-vṛtti-nirodhaḥ</p>
          <p className="text-gray-600">
            Yoga is the cessation of the fluctuations of the mind.
          </p>
          <footer className="mt-3">
            <Link
              to="/pada/samadhi-pada/sutra/2"
              className="text-amber-600 hover:text-amber-800 text-sm font-medium"
            >
              — Sutra 1.2 →
            </Link>
          </footer>
        </blockquote>
      </section>
    </div>
  );
}
