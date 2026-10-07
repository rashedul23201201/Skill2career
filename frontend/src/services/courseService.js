import api from "./api";

/**
 * Service handling LMS course management, discovery catalog, and curriculum authoring (SKL-53).
 */
export const courseService = {
  /**
   * Fetch paginated courses with optional filters (category, level, search, my_courses, status).
   */
  async getCourses(params = {}) {
    const response = await api.get("/courses", { params });
    return response.data;
  },

  /**
   * Fetch single course details including module syllabus and lesson attachments.
   */
  async getCourseById(courseId) {
    const response = await api.get(`/courses/${courseId}`);
    return response.data;
  },

  /**
   * Create a new course curriculum container (Instructor / Admin).
   */
  async createCourse(courseData) {
    const response = await api.post("/courses", courseData);
    return response.data;
  },

  /**
   * Update existing course metadata.
   */
  async updateCourse(courseId, courseData) {
    const response = await api.put(`/courses/${courseId}`, courseData);
    return response.data;
  },

  /**
   * Delete a course and its curriculum tree.
   */
  async deleteCourse(courseId) {
    const response = await api.delete(`/courses/${courseId}`);
    return response.data;
  },

  /**
   * Toggle publication status or apply administrative moderation.
   */
  async updateCourseStatus(courseId, { status, reason = "" }) {
    const response = await api.patch(`/courses/${courseId}/status`, {
      status,
      reason,
    });
    return response.data;
  },

  /**
   * Synchronize the complete curriculum outline (modules and lessons).
   */
  async syncCurriculum(courseId, modules) {
    const response = await api.put(`/courses/${courseId}/curriculum`, { modules });
    return response.data;
  },
};

export default courseService;
