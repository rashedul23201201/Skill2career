import api from "./api";

export const enrollmentService = {
  async enrollInCourse(courseId) {
    const response = await api.post(`/courses/${courseId}/enroll`);
    return response.data;
  },

  async getEnrollmentStatus(courseId) {
    const response = await api.get(`/courses/${courseId}/enrollment-status`);
    return response.data;
  },

  async getCourseProgress(courseId) {
    const response = await api.get(`/courses/${courseId}/progress`);
    return response.data;
  },

  async completeLesson(lessonId, isCompleted = true) {
    const response = await api.post(`/lessons/${lessonId}/complete`, {
      is_completed: isCompleted,
    });
    return response.data;
  },

  async getEnrolledCourses(status) {
    const params = status ? { status } : {};
    const response = await api.get("/learners/enrolled-courses", { params });
    return response.data;
  },
};

export default enrollmentService;
