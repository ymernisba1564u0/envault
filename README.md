# envault

> A lightweight secrets manager that encrypts `.env` files using age encryption for local and CI environments.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envault
```

---

## Usage

**Encrypt a `.env` file:**

```bash
envault encrypt .env --output .env.age
```

**Decrypt at runtime:**

```bash
envault decrypt .env.age --output .env
```

**Inject secrets directly into a command:**

```bash
envault run --secrets .env.age -- python app.py
```

**Generate a new age key pair:**

```bash
envault keygen
```

Keys are stored in `~/.config/envault/keys` by default. Set `ENVAULT_KEY` in your CI environment to use a specific private key for decryption.

---

## How It Works

envault wraps [age](https://github.com/FiloSottile/age) encryption to protect your `.env` files at rest. Encrypted `.env.age` files are safe to commit to version control. Secrets are only decrypted when needed, keeping plaintext exposure minimal.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

[MIT](LICENSE)