import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import dotenv from 'dotenv';
import jwt from 'jsonwebtoken';

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

const PORT = process.env.PORT || 5001;


app.use('/health_check', (_req, res) => res.json({ ok: true, service: 'user-service' }));

// app.use('v1/')


app.listen(PORT, () => {
  console.log(`workouts-service listening on :${PORT}`);
});