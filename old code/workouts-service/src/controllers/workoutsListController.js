import Workout from '../models/Workout.js';


function listWorkouts(req, res) {
    const userId = req.user.id; // Assuming req.user is set by authentication middleware

    const { page = 1, limit = 10 } = req.query;
    const skip = (page - 1) * limit;
    try {
        const list = Workout.find({ userId })
            .skip(parseInt(skip))
            .limit(parseInt(limit))
            .then(workouts => res.json({ workouts }))
            .catch(err => res.status(500).json({ error: 'Internal server error' }));
        return res.status(200).json({ success: true, message: 'list featched successfully', data: list });
    } catch (error) {
        console.error(error);
        return res.status(500).json({ message: "Internal server error" });
    }
}

function suggestWorkout(req, res) {
    
}
module.exports = { listWorkouts };