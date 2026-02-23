import express from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { body, validationResult } from "express-validator";
import User from "../models/User.js";
import { logIn, logOut, signUp, profileComplete } from "../controllers/authController.js";

const router = express.Router();

router.get('/my-workouts', )