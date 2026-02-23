import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
    title: {
        type: String,
        required: true,
        trim: true
    },
    description: {
        type: String,
        required: false,
        trim: true
    },
    workoutType: {
        type: String,
        enum: ['cardio', 'strength', 'flexibility', 'balance', 'muscle growth', 'endurance', 'conditioning', 'mobility'],
        required: true
    },
    primaryMuscleGroup: {
        type: String,
        enum: ['chest', 'back', 'legs', 'arms', 'shoulders', 'core', 'full body'],
        required: true
    },
    secondaryMuscleGroup: {
        type: [String],
        enum: ['chest', 'back', 'legs', 'arms', 'shoulders', 'core', 'full body'],
        required: false,
        default: []
    },
    durationMinutes: {
        type: Number,
        required: true,
        min: 1,
        max: 300
    },
    intensityLevel: {
        type: String,
        enum: ['low', 'medium', 'high'],
        required: true
    },
    equipmentNeeded: {
        type: [String],
        enum: ['none', 'dumbbells', 'barbell', 'kettlebell', 'resistance bands', 'machine', 'bodyweight',],
        required: true,
        default: ['none']
    },
    movementVariety: {
        type: [String],
        enum: ['unilateral', 'bilateral', 'compound', 'isolation'],
        required: false,
        default: []
    },
    frequencyPerWeek: {
        type: Number,
        required: true,
        min: 1,
        max: 14
    },
    workoutLevel: {
        type: String,
        enum: ['Beginner', 'Intermediate', 'Advanced'],
        required: true
    },
    demoUrl: {
        type: String,
        required: false,
        trim: true
    },
}, { timestamps: true});

export const Workout = mongoose.model('Workout', userSchema);