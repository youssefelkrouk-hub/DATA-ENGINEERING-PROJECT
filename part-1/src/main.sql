-- 2. EXPLORATION GÉNÉRALE
-- ============================================================
 
-- Voir toutes les lignes
SELECT * FROM employees;
 
-- Compter le nombre total d'employés
SELECT COUNT(*) AS total_employees FROM employees;
 
-- Voir les 10 premières lignes juste pour vérifier la structure de la table
SELECT * FROM employees LIMIT 10;
 
-- Structure des colonnes (types, nullable...)
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'employees';
 
 
-- ============================================================
-- 3. RECHERCHE / FILTRAGE
-- ============================================================
 
-- Employés d'un pays donné
SELECT * FROM employees
WHERE country_code = 'ID';
 
-- Employés d'une entreprise donnée
SELECT * FROM employees
WHERE company_name ILIKE '%tech%';
 
-- Employés avec plus de X années d'expérience
SELECT * FROM employees
WHERE years_experience > 5
ORDER BY years_experience DESC;
 
-- Recherche par nom (insensible à la casse)
SELECT * FROM employees
WHERE first_name ILIKE '%karim%' OR last_name ILIKE '%karim%';
 
-- Employés sans email renseigné
SELECT * FROM employees
WHERE email IS NULL OR email = '';
 
 
-- ============================================================
-- 4. AGRÉGATIONS / STATISTIQUES
-- ============================================================
 
-- Nombre d'employés par pays
SELECT country_code, COUNT(*) AS nb_employees
FROM employees
GROUP BY country_code
ORDER BY nb_employees DESC;
 
-- Nombre d'employés par département
SELECT departement, COUNT(*) AS nb_employees
FROM employees
GROUP BY departement
ORDER BY nb_employees DESC;
 
-- Moyenne d'années d'expérience par job_title
SELECT job_title, ROUND(AVG(years_experience), 1) AS avg_experience
FROM employees
GROUP BY job_title
ORDER BY avg_experience DESC;
 
-- Répartition par genre
SELECT gender, COUNT(*) AS nb_employees
FROM employees
GROUP BY gender;
 
-- Top 5 des entreprises qui emploient le plus de monde
SELECT company_name, COUNT(*) AS nb_employees
FROM employees
GROUP BY company_name
ORDER BY nb_employees DESC
LIMIT 5;
 
 
-- ============================================================
-- 5. TRI
-- ============================================================
 
-- Employés triés par années d'expérience décroissante
SELECT first_name, last_name, years_experience
FROM employees
ORDER BY years_experience DESC;
 
-- Employés triés par nom alphabétique
SELECT first_name, last_name
FROM employees
ORDER BY last_name ASC, first_name ASC;
 
 
-- ============================================================
-- 6. MISE À JOUR / SUPPRESSION (à utiliser avec précaution)
-- ============================================================
 
-- Mettre à jour le job_title d'un employé précis
UPDATE employees
SET job_title = 'Data Engineer',company_name = 'BCGX'
WHERE id = 1;
SELECT * FROM employees WHERE id = 1;
-- Supprimer un employé précis
-- DELETE FROM employees
-- WHERE id = 1;
 
-- Vider complètement la table (⚠️ irréversible)
TRUNCATE TABLE employees;
SELECT * FROM employees;

 
 
-- ============================================================
-- 7. VÉRIFICATION DES DOUBLONS
-- ============================================================
 
-- Vérifier s'il y a des emails en double
SELECT email, COUNT(*) AS occurrences
FROM employees
GROUP BY email
HAVING COUNT(*) > 1;
 
-- Vérifier s'il y a des id dupliqués (ne devrait jamais arriver, id = PRIMARY KEY)
SELECT id, COUNT(*) AS occurrences
FROM employees
GROUP BY id
HAVING COUNT(*) > 1;
 