class CustomNavbar extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        nav {
          background: rgba(0, 0, 0, 0.8);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          position: sticky;
          top: 0;
          z-index: 50;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
.logo {
          color: white;
-webkit-background-clip: text;
          background-clip: text;
          color: transparent;
          font-weight: bold;
          font-size: 1.5rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        ul { 
          display: flex; 
          gap: 1.5rem; 
          list-style: none; 
          margin: 0; 
          padding: 0; 
        }
        a { 
          color: rgb(226, 232, 240);
          text-decoration: none;
          transition: all 0.2s;
          font-weight: 500;
          position: relative;
        }
        a:hover {
          color: white;
}
        a::after {
          content: '';
          position: absolute;
          bottom: -4px;
          left: 0;
          width: 0;
          height: 2px;
          background: white;
transition: width 0.3s;
        }
        a:hover::after {
          width: 100%;
        }
        @media (max-width: 768px) {
          nav {
            flex-direction: column;
            gap: 1rem;
            padding: 1rem;
          }
          ul {
            width: 100%;
            justify-content: center;
          }
        }
      </style>
      <nav>
        <a href="/" class="logo">
          <i data-feather="image"></i>
          FetchX
        </a>
        <ul>
          <li><a href="https://github.com/wyv9">by wyv :3</a></li>
</ul>
      </nav>
    `;
  }
}
customElements.define('custom-navbar', CustomNavbar);