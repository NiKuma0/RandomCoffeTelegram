---- Set on delete
-- On delete "set null" 
ALTER TABLE public.user
DROP CONSTRAINT user__profession_id_fkey;
ALTER TABLE public.user  
ADD CONSTRAINT user__profession_id_fkey FOREIGN KEY (_profession_id) REFERENCES public.profession (id) ON DELETE SET NULL;  

-- On delete "cascade" 
ALTER TABLE public.pair
DROP CONSTRAINT pair_hr_id_fkey;
ALTER TABLE public.pair
ADD CONSTRAINT pair_hr_id_fkey FOREIGN KEY (hr_id) REFERENCES public.user (teleg_id) ON DELETE CASCADE;

-- On delte "cascade"
ALTER TABLE public.pair
DROP CONSTRAINT pair_respondent_id_fkey;
ALTER TABLE public.pair
ADD CONSTRAINT pair_respondent_id_fkey FOREIGN KEY (respondent_id) REFERENCES public.user (teleg_id) ON DELETE CASCADE;

-- Change type of user.status field

-- ALTER TABLE public.user
-- ADD TABLE
