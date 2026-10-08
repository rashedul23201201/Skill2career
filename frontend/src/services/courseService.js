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

  /**
   * Fetch all lessons for a course (SKL-55).
   */
  async getCourseLessons(courseId) {
    const response = await api.get(`/courses/${courseId}/lessons`);
    return response.data;
  },

  /**
   * Fetch single lesson details and attached study materials (SKL-55).
   */
  async getLessonById(lessonId) {
    const response = await api.get(`/lessons/${lessonId}`);
    return response.data;
  },

  /**
   * Create a new lesson under a course (SKL-55 AC-1).
   */
  async createLesson(courseId, lessonData) {
    const response = await api.post(`/courses/${courseId}/lessons`, lessonData);
    return response.data;
  },

  /**
   * Update an existing lesson and its study materials (SKL-55 AC-2).
   */
  async updateLesson(lessonId, lessonData) {
    const response = await api.put(`/lessons/${lessonId}`, lessonData);
    return response.data;
  },

  /**
   * Delete a lesson (SKL-55 AC-5).
   */
  async deleteLesson(lessonId) {
    const response = await api.delete(`/lessons/${lessonId}`);
    return response.data;
  },

  /**
   * Upload study material document for a lesson (SKL-55 AC-2).
   */
  async uploadLessonMaterial(lessonId, file) {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post(`/lessons/${lessonId}/materials`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Remove a study material attachment from a lesson.
   */
  async deleteLessonMaterial(lessonId, filename) {
    const response = await api.delete(`/lessons/${lessonId}/materials/${filename}`);
    return response.data;
  },

  /**
   * Add a new module to a course.
   */
  async createModule(courseId, moduleData) {
    const response = await api.post(`/courses/${courseId}/modules`, moduleData);
    return response.data;
  },

  /**
   * Update an existing module.
   */
  async updateModule(moduleId, moduleData) {
    const response = await api.put(`/courses/modules/${moduleId}`, moduleData);
    return response.data;
  },

  /**
   * Delete a curriculum module.
   */
  async deleteModule(moduleId) {
    const response = await api.delete(`/courses/modules/${moduleId}`);
    return response.data;
  },
};

export default courseService;
